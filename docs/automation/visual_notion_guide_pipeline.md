# Headless Visual User Guide Automation Pipeline

## Architecture Overview
1. **Runner**: Python with `playwright` (Chromium headless driver).
2. **Target UI**: Any local or remote web dashboard / UI port.
3. **Artifacts**: High-DPI UI snapshots stored in structured asset folders (`docs/screenshots/`).
4. **Publisher**: Notion API (`notion-client`) embedding rich text, callouts, and visual blocks.

---

## 1. Automation Script (`scripts/generate_visual_guide.py`)

```python
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("docs/screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STEPS = [
    {
        "id": "01_dashboard_landing",
        "selector": "#hero-banner",
        "action": None,
        "title": "1. Accessing the Dashboard",
        "desc": "Open the platform URL to view live telemetry and initial ingest status."
    },
    {
        "id": "02_kmeans_clustering",
        "selector": "#cluster-chart-container",
        "action": "click_cluster_tab",
        "title": "2. Visualizing K-Means Clusters",
        "desc": "Inspect PCA 2D/3D projections of clustered tickers with automated centroid profiles."
    },
    {
        "id": "03_topsis_weight_tuning",
        "selector": "#topsis-control-panel",
        "action": "adjust_sliders",
        "title": "3. Configuring Multi-Criteria Decision Weights",
        "desc": "Tune criteria priorities or apply predefined investor profiles."
    },
    {
        "id": "04_topsis_rankings",
        "selector": "#topsis-ranking-table",
        "action": None,
        "title": "4. Evaluating Quantitative Rankings",
        "desc": "Review relative closeness scores ($C_i$) and algorithmic recommendations."
    }
]

async def capture_walkthrough():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        page = await context.new_page()

        print("[Guide Engine] Navigating to Dashboard...")
        await page.goto("http://localhost:8000", wait_until="networkidle")

        for step in STEPS:
            shot_path = OUTPUT_DIR / f"{step['id']}.png"
            if step["selector"]:
                element = await page.wait_for_selector(step["selector"])
                await element.screenshot(path=str(shot_path))
            else:
                await page.screenshot(path=str(shot_path), full_page=False)
            print(f"[Captured] {shot_path}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_walkthrough())
```

---

## 2. Notion Publisher (`scripts/sync_to_notion.py`)

```python
import os
from notion_client import Client

notion = Client(auth=os.environ.get("NOTION_API_KEY"))
PAGE_ID = os.environ.get("NOTION_GUIDE_PAGE_ID")

def push_guide_to_notion(steps_data):
    for step in steps_data:
        # 1. Heading
        notion.blocks.children.append(
            block_id=PAGE_ID,
            children=[{
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": step["title"]}}]}
            }]
        )
        # 2. Description Paragraph
        notion.blocks.children.append(
            block_id=PAGE_ID,
            children=[{
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": step["desc"]}}]}
            }]
        )
        # 3. Image Block attachment via S3/Cloudinary/Signed URL
        # (Pass uploaded image URL into Notion Image block)
```
