"""
Scraper otomatis untuk mengunduh laporan keuangan tahunan (.xlsx) dari IDX.
Memanfaatkan Playwright headless dengan Microsoft Edge untuk menangani
sesi dan tantangan Cloudflare/WAF pada endpoint resmi BEI.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin

from playwright.async_api import (
    Browser,
    BrowserContext,
    Download,
    Page,
    async_playwright,
)

IDX_PAGE_URL = "https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan"
IDX_API_URL = "https://www.idx.co.id/primary/ListedCompany/GetFinancialReport"

IDX_ORIGIN = "https://www.idx.co.id"

# Project root = folder tempat downloader.py berada.
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
TEMP_DIR = DATA_DIR / "temp_downloads"
LOG_FILE = RAW_DIR / "download_log.csv"

# Scope penelitian
RESEARCH_SCOPE_MIN = 2020
RESEARCH_SCOPE_MAX = 2025

# Batas aman default. Pengguna dapat menaikkan sampai 10.
DEFAULT_WORKERS = 3
MAX_WORKERS = 10
DEFAULT_DELAY = 0.75

# Regex fleksibel terhadap separator '-' atau spasi.
# Contoh yang diterima:
#   FinancialStatement-2022-Tahunan-ASII.xlsx
#   FinancialStatement 2022 Tahunan ASII.xlsx
ANNUAL_XLSX_RE = re.compile(
    r"financialstatement[\s_-]*{year}[\s_-]*tahunan[\s_-]*{ticker}\s*\.xlsx$",
    re.IGNORECASE,
)

QUARTER_MARKER_RE = re.compile(
    r"(?:\bI\b|\bII\b|\bIII\b|TW1|TW2|TW3|Q1|Q2|Q3)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Job:
    ticker: str
    years: tuple[int, ...]


@dataclass
class ResultRow:
    ticker: str
    year: int
    status: str
    filename: str = ""
    path: str = ""
    message: str = ""


def ensure_dir(path: Path) -> Path:
    """Memastikan direktori ada. Melempar error dengan path aktual jika gagal."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        raise RuntimeError(f"Gagal membuat direktori {path}: {exc}") from exc
    return path


def parse_tickers(value: str) -> list[str]:
    """Parse ticker list from comma/space/semicolon separated text."""
    parts = re.split(r"[,;\s]+", value.strip().upper())
    tickers = []
    seen = set()
    for part in parts:
        if not part:
            continue
        if not re.fullmatch(r"[A-Z0-9.\-]{1,20}", part):
            raise ValueError(f"Kode saham tidak valid: {part!r}")
        if part not in seen:
            tickers.append(part)
            seen.add(part)
    if not tickers:
        raise ValueError("Tidak ada kode saham yang diberikan.")
    return tickers


def parse_years(value: str) -> list[int]:
    """
    Accept:
      2022
      2020,2021,2022
      2020-2024
      2020,2022-2024
    """
    years: set[int] = set()
    tokens = re.split(r"[,;\s]+", value.strip())
    for token in tokens:
        if not token:
            continue
        if re.fullmatch(r"\d{4}-\d{4}", token):
            start, end = map(int, token.split("-"))
            if start > end:
                start, end = end, start
            years.update(range(start, end + 1))
        elif re.fullmatch(r"\d{4}", token):
            years.add(int(token))
        else:
            raise ValueError(f"Format tahun tidak valid: {token!r}")

    years_list = sorted(years)
    if not years_list:
        raise ValueError("Tidak ada tahun yang diberikan.")

    for year in years_list:
        if year < 2000 or year > 2100:
            raise ValueError(f"Tahun di luar rentang yang diizinkan: {year}")

    out_of_scope = [y for y in years_list if y < RESEARCH_SCOPE_MIN or y > RESEARCH_SCOPE_MAX]
    if out_of_scope:
        print(
            f"WARNING: Tahun {', '.join(map(str, out_of_scope))} di luar scope penelitian default "
            f"({RESEARCH_SCOPE_MIN}–{RESEARCH_SCOPE_MAX})."
        )

    return years_list


def clean_filename(name: str) -> str:
    """Remove path separators / invalid Windows filename chars."""
    name = Path(name).name
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name.strip() or "download.xlsx"


def build_api_url(ticker: str, year: int, periode: str) -> str:
    """Build the official IDX GetFinancialReport query used by the web UI."""
    params = {
        "indexFrom": 1,
        "pageSize": 20,
        "year": year,
        "reportType": "rdf",
        "EmitenType": "s",
        "periode": periode,
        "kodeEmiten": ticker,
        "SortColumn": "KodeEmiten",
        "SortOrder": "asc",
    }
    return f"{IDX_API_URL}?{urlencode(params)}"


def absolute_url(path_or_url: str) -> str:
    return urljoin(IDX_ORIGIN, str(path_or_url))


def extract_json_payload(raw_text: str) -> dict[str, Any]:
    """Parse JSON with a helpful error when IDX returns HTML/challenge text."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        snippet = re.sub(r"\s+", " ", raw_text[:300])
        raise RuntimeError(
            "IDX tidak mengembalikan JSON. Kemungkinan halaman challenge/403 "
            f"atau layanan sedang membatasi request. Respons awal: {snippet!r}"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError("Respons IDX bukan object JSON yang diharapkan.")
    return data


def get_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("Results", [])
    if not isinstance(results, list):
        return []
    return [item for item in results if isinstance(item, dict)]


def find_matching_company(results: list[dict[str, Any]], ticker: str) -> dict[str, Any] | None:
    ticker_upper = ticker.upper()
    for item in results:
        if str(item.get("KodeEmiten", "")).upper() == ticker_upper:
            return item
    return None


def choose_annual_xlsx(
    company_item: dict[str, Any],
    ticker: str,
    year: int,
) -> tuple[str, str] | None:
    """
    Return (filename, absolute_url) for the best matching annual XLSX.

    Priority:
    1. Exact FinancialStatement + year + Tahunan + ticker filename.
    2. XLSX containing year + Tahunan + ticker, while excluding quarter markers.
    """
    attachments = company_item.get("Attachments", [])
    if not isinstance(attachments, list):
        return None

    candidates: list[tuple[str, str]] = []

    exact_pattern = re.compile(
        ANNUAL_XLSX_RE.pattern.format(year=re.escape(str(year)), ticker=re.escape(ticker)),
        re.IGNORECASE,
    )

    fallback_tokens = [str(year).lower(), "tahunan", ticker.lower()]

    for attachment in attachments:
        if not isinstance(attachment, dict):
            continue

        filename = str(attachment.get("File_Name", "")).strip()
        filepath = str(attachment.get("File_Path", "")).strip()
        filetype = str(attachment.get("File_Type", "")).lower().strip()

        if not filename or not filepath:
            continue
        is_xlsx = filename.lower().endswith(".xlsx") or filetype in {".xlsx", "xlsx"}
        if not is_xlsx:
            continue

        lower_name = filename.lower()

        # 1) exact expected naming pattern
        if exact_pattern.fullmatch(filename):
            return clean_filename(filename), absolute_url(filepath)

        # 2) fallback: must mention year/tahunan/ticker and must not look quarterly
        if all(token in lower_name for token in fallback_tokens):
            if QUARTER_MARKER_RE.search(filename.replace("FinancialStatement", "")):
                continue
            candidates.append((clean_filename(filename), absolute_url(filepath)))

    if candidates:
        # Deterministic order.
        candidates.sort(key=lambda item: item[0].lower())
        return candidates[0]

    return None


def attachment_names(company_item: dict[str, Any]) -> list[str]:
    names: list[str] = []
    attachments = company_item.get("Attachments", [])
    if isinstance(attachments, list):
        for att in attachments:
            if isinstance(att, dict) and att.get("File_Name"):
                names.append(str(att["File_Name"]))
    return names


async def fetch_idx_json(page: Page, url: str) -> dict[str, Any]:
    """
    Fetch same-origin IDX JSON from inside the browser.

    Doing this in a real browser is intentional: plain Python requests may be
    challenged by IDX's anti-bot layer, while browser requests can complete
    the site challenge in the normal way.
    """
    js = """
    async ({url}) => {
        const response = await fetch(url, {
            method: "GET",
            cache: "no-store",
            credentials: "include",
            headers: {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        });
        const text = await response.text();
        return {status: response.status, text};
    }
    """

    for attempt in range(2):
        response = await page.evaluate(js, {"url": url})
        status = int(response.get("status", 0))
        text = str(response.get("text", ""))

        if status == 200:
            return extract_json_payload(text)

        if attempt == 0 and status in {403, 429, 500, 502, 503, 504}:
            await page.wait_for_timeout(2500)
            continue

        snippet = re.sub(r"\s+", " ", text[:250])
        raise RuntimeError(f"IDX API HTTP {status}. Respons: {snippet!r}")

    raise RuntimeError("Gagal mengambil data IDX.")


async def create_page(browser: Browser, headless: bool) -> tuple[BrowserContext, Page]:
    """Create a browser context and warm up the official IDX page."""
    context = await browser.new_context(
        accept_downloads=True,
        locale="id-ID",
        timezone_id="Asia/Jakarta",
    )
    page = await context.new_page()

    # The official page is used to establish a normal browser session/challenge.
    await page.goto(IDX_PAGE_URL, wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_timeout(1500 if not headless else 500)
    return context, page


async def download_file_with_page(
    page: Page,
    file_url: str,
    temp_path: Path,
) -> None:
    """Fetch the XLSX as a browser download and save it to a temporary path."""
    ensure_dir(temp_path.parent)

    # Download the file through a same-origin browser fetch -> Blob -> anchor.
    # This avoids depending on Content-Disposition behavior of direct navigation.
    download_script = """
    async ({url, filename}) => {
        const response = await fetch(url, {
            method: "GET",
            cache: "no-store",
            credentials: "include"
        });
        if (!response.ok) {
            const body = await response.text();
            throw new Error(`File download HTTP ${response.status}: ${body.slice(0, 180)}`);
        }
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = objectUrl;
        a.download = filename;
        a.style.display = "none";
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            URL.revokeObjectURL(objectUrl);
            a.remove();
        }, 5000);
    }
    """

    async with page.expect_download(timeout=120000) as download_info:
        await page.evaluate(
            download_script,
            {"url": file_url, "filename": temp_path.name},
        )

    download: Download = await download_info.value
    await download.save_as(str(temp_path))


async def download_one_year(
    page: Page,
    ticker: str,
    year: int,
    temp_dir: Path,
    delay: float,
) -> ResultRow:
    """Search IDX for one annual report and download its XLSX."""
    # On IDX web UI, audited annual statement uses periode='audit'.
    periods_to_try = ["audit", "tahunan"]
    last_error = ""

    for period in periods_to_try:
        api_url = build_api_url(ticker, year, period)
        try:
            payload = await fetch_idx_json(page, api_url)
        except Exception as exc:
            last_error = str(exc)
            continue

        results = get_results(payload)
        item = find_matching_company(results, ticker)
        if not item:
            last_error = (
                f"Emiten {ticker} tidak ditemukan pada respons IDX untuk {year} "
                f"(periode={period})."
            )
            continue

        selected = choose_annual_xlsx(item, ticker, year)
        if not selected:
            names = ", ".join(attachment_names(item))
            last_error = (
                f"Lampiran XLSX tahunan tidak ditemukan untuk {ticker} {year}. "
                f"Lampiran yang tersedia: {names or '(tidak ada)'}"
            )
            continue

        filename, file_url = selected
        temp_path = temp_dir / ticker / filename

        try:
            await download_file_with_page(page, file_url, temp_path)
        except Exception as exc:
            last_error = f"Download XLSX gagal: {exc}"
            continue

        if not temp_path.exists() or temp_path.stat().st_size == 0:
            last_error = "File berhasil dipicu tetapi hasil file kosong/tidak ditemukan."
            continue

        # Basic XLSX signature check. An XLSX is a ZIP file and starts with PK.
        file_size = temp_path.stat().st_size
        with temp_path.open("rb") as fh:
            signature = fh.read(2)
        if signature != b"PK":
            last_error = (
                f"File di server IDX rusak/corrupt (ukuran {file_size} bytes, bukan format XLSX/ZIP valid). "
                f"Data tahun ini dapat diperoleh secara otomatis dari kolom komparatif Prior Year laporan tahun berikutnya."
            )
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            break

        return ResultRow(
            ticker=ticker,
            year=year,
            status="OK",
            filename=filename,
            path=str(temp_path),
            message=f"periode={period}",
        )

        # Delay applies after successful/failed query cycle too.
    await asyncio.sleep(delay)
    return ResultRow(
        ticker=ticker,
        year=year,
        status="FAILED",
        message=last_error or "Unknown error",
    )


async def process_stock(
    browser: Browser,
    job: Job,
    workers_lock: asyncio.Semaphore,
    temp_root: Path,
    delay: float,
    headless: bool,
) -> list[ResultRow]:
    """Process all requested years for one ticker in one browser context."""
    async with workers_lock:
        print(f"\n[{job.ticker}] START — tahun: {', '.join(map(str, job.years))}")

        context: BrowserContext | None = None
        try:
            context, page = await create_page(browser, headless=headless)
            rows: list[ResultRow] = []
            ticker_temp = temp_root / job.ticker
            ensure_dir(ticker_temp)

            for year in job.years:
                # Skip if a completed file for this year already exists in raw.
                existing_dir = RAW_DIR / job.ticker
                existing_matches = list(existing_dir.glob(f"*{year}*Tahunan*{job.ticker}*.xlsx")) if existing_dir.exists() else []
                if existing_matches:
                    path = existing_matches[0]
                    row = ResultRow(
                        ticker=job.ticker,
                        year=year,
                        status="SKIPPED",
                        filename=path.name,
                        path=str(path),
                        message="File sudah ada",
                    )
                    rows.append(row)
                    print(f"[{job.ticker}] {year} SKIP — {path.name}")
                    continue

                row = await download_one_year(
                    page=page,
                    ticker=job.ticker,
                    year=year,
                    temp_dir=temp_root,
                    delay=delay,
                )
                rows.append(row)

                if row.status == "OK":
                    # Requirement: the final ticker folder is created when the
                    # first file for that ticker has completed.
                    final_dir = RAW_DIR / job.ticker
                    ensure_dir(final_dir)
                    src = Path(row.path)
                    destination = final_dir / row.filename
                    shutil.move(str(src), str(destination))
                    row.path = str(destination)

                    print(
                        f"[{job.ticker}] {year} OK   — {row.filename}"
                    )
                    print(f"[{job.ticker}] saved -> {destination}")
                else:
                    print(f"[{job.ticker}] {year} FAIL — {row.message}")

                await asyncio.sleep(delay)

            # Remove temporary ticker folder if empty.
            try:
                ticker_temp.rmdir()
            except OSError:
                pass

            return rows

        except Exception as exc:
            message = f"Worker {job.ticker} gagal: {exc}"
            print(f"[{job.ticker}] ERROR — {message}")
            return [
                ResultRow(
                    ticker=job.ticker,
                    year=year,
                    status="FAILED",
                    message=message,
                )
                for year in job.years
            ]
        finally:
            if context is not None:
                await context.close()


def write_log(rows: list[ResultRow]) -> None:
    ensure_dir(RAW_DIR)
    file_exists = LOG_FILE.exists()

    with LOG_FILE.open("a", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "timestamp",
                "ticker",
                "year",
                "status",
                "filename",
                "path",
                "message",
            ],
        )
        if not file_exists:
            writer.writeheader()

        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        for row in rows:
            writer.writerow(
                {
                    "timestamp": timestamp,
                    "ticker": row.ticker,
                    "year": row.year,
                    "status": row.status,
                    "filename": row.filename,
                    "path": row.path,
                    "message": row.message,
                }
            )


def read_stocks_file(path: str) -> list[str]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File saham tidak ditemukan: {file_path}")
    text = file_path.read_text(encoding="utf-8")
    return parse_tickers(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download Financial Statement Tahunan IDX ke data/raw/<TICKER>/"
    )
    parser.add_argument(
        "--stocks",
        help="Kode saham, pisahkan koma. Contoh: ASII,UNTR,TLKM",
    )
    parser.add_argument(
        "--stocks-file",
        help="File txt berisi satu/lebih kode saham.",
    )
    parser.add_argument(
        "--years",
        help="Tahun atau range. Contoh: 2022 atau 2020-2024",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Jumlah saham yang diproses bersamaan (default {DEFAULT_WORKERS}, max {MAX_WORKERS}).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help=f"Jeda antar download dalam detik (default {DEFAULT_DELAY}).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Jalankan Edge tanpa menampilkan jendela browser.",
    )
    return parser


def interactive_inputs() -> tuple[list[str], list[int]]:
    print("=" * 64)
    print("IDX Financial Statement Downloader")
    print("Periode yang dicari: TAHUNAN")
    print("=" * 64)
    stocks_text = input(
        "Kode saham (contoh ASII,UNTR,TLKM): "
    ).strip()
    years_text = input(
        "Tahun (contoh 2022 atau 2020-2024): "
    ).strip()
    return parse_tickers(stocks_text), parse_years(years_text)


async def async_main(args: argparse.Namespace) -> int:
    # Determine stock list.
    if args.stocks:
        tickers = parse_tickers(args.stocks)
    elif args.stocks_file:
        tickers = read_stocks_file(args.stocks_file)
    else:
        tickers, interactive_years = interactive_inputs()
        args.years = args.years or ",".join(map(str, interactive_years))

    if not args.years:
        raise ValueError("--years belum diisi.")
    years = parse_years(args.years)

    if not 1 <= args.workers <= MAX_WORKERS:
        raise ValueError(
            f"--workers harus antara 1 sampai {MAX_WORKERS}."
        )
    if args.delay < 0:
        raise ValueError("--delay tidak boleh negatif.")

    ensure_dir(RAW_DIR)
    ensure_dir(TEMP_DIR)

    print("\nKonfigurasi:")
    print(f"  Saham     : {', '.join(tickers)}")
    print(f"  Tahun     : {', '.join(map(str, years))}")
    print("  Periode   : Tahunan")
    print("  Tipe      : Financial Statement (rdf)")
    print(f"  Workers   : {args.workers} saham sekaligus")
    print(f"  Output    : {RAW_DIR}")
    print("  Browser   : Microsoft Edge + Playwright")
    print()

    jobs = [Job(ticker=ticker, years=tuple(years)) for ticker in tickers]
    semaphore = asyncio.Semaphore(args.workers)

    results: list[ResultRow] = []

    async with async_playwright() as playwright:
        # Use installed Microsoft Edge on Windows.
        try:
            browser = await playwright.chromium.launch(
                channel="msedge",
                headless=args.headless,
                ignore_default_args=["--enable-automation"],
                args=["--disable-blink-features=AutomationControlled"],
            )
        except Exception as exc:
            raise RuntimeError(
                "Microsoft Edge tidak bisa dibuka oleh Playwright. "
                "Pastikan Edge terpasang dan jalankan: py -m pip install playwright"
            ) from exc

        try:
            tasks = [
                process_stock(
                    browser=browser,
                    job=job,
                    workers_lock=semaphore,
                    temp_root=TEMP_DIR,
                    delay=args.delay,
                    headless=args.headless,
                )
                for job in jobs
            ]
            groups = await asyncio.gather(*tasks)
            for group in groups:
                results.extend(group)
        finally:
            await browser.close()

    write_log(results)

    # Summary.
    ok = sum(r.status == "OK" for r in results)
    skipped = sum(r.status == "SKIPPED" for r in results)
    failed = sum(r.status == "FAILED" for r in results)

    print("\n" + "=" * 64)
    print("SELESAI")
    print("=" * 64)
    print(f"Berhasil : {ok}")
    print(f"Skip     : {skipped}")
    print(f"Gagal    : {failed}")
    print(f"Log      : {LOG_FILE}")

    if failed:
        print("\nFile yang gagal:")
        for row in results:
            if row.status == "FAILED":
                print(f"  - {row.ticker} {row.year}: {row.message}")
        print(
            "\nCoba ulang ticker/tahun yang gagal dengan --workers 1 "
            "untuk debugging."
        )

    # Do not hide failure behind exit code 0.
    return 1 if failed and ok == 0 else 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\nDihentikan oleh pengguna.")
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
