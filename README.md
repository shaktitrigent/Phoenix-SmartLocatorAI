# Phoenix Smart Locator AI

Unified, zero-setup pipeline to scan a page (URL or HTML), generate robust locators (CSS/XPath/Playwright Role), score stability, flag dynamics/duplicates, validate in a real browser (optional with auth), and export ready-to-use Page Objects and reports.

## Features

- DOM scan (requests/BeautifulSoup; optional Playwright render)
- Locator generation: CSS, XPath, Playwright getByRole/getByText
- Stability scoring (1–10) + High/Medium/Low labels
- Dynamic/duplicate detection + warnings
- Framework compatibility tagging (Playwright/Selenium/Both)
- Code snippets per locator (Playwright/Selenium)
- Optional real-browser validation with auth (Playwright)
- Exports: Markdown report, JSON, Page Objects (Playwright/Selenium)

## Install

```bash
pip install -r requirements.txt
```

## Quick Start (Unified Pipeline)

```bash
# From URL (no auth), export both POMs, keep Medium+ stability
python smart_locator_ai.py \
  --url https://example.com \
  --framework both \
  --min-stability Medium

# From local HTML
python smart_locator_ai.py --file ./page.html --framework playwright
```

Outputs are written to `exports/`:
- `report.md` (summary + markdown table)
- `locators.json` (integration-ready with metadata)
- `page.py` (standardized Page Object for primary framework)
- `<ClassName>_Playwright.py` and/or `<ClassName>_Selenium.py` (framework-specific)

### Integration-Ready JSON Format

The `locators.json` file includes comprehensive metadata for integration:

```json
{
  "metadata": {
    "generated_at": "2025-11-10T12:37:38.133894",
    "source": "https://example.com",
    "total_elements": 10,
    "total_locators": 25,
    "framework": "both",
    "min_stability": "Medium",
    "validated": true,
    "ai_enriched": false,
    "class_name": "ProductPage"
  },
  "summary": {
    "total_elements": 10,
    "locator_distribution": {"css": 15, "xpath": 8, "role": 2},
    "framework_split": {"playwright": 10, "selenium": 8, "both": 7},
    "stability": {"high": 12, "medium": 10, "low": 3}
  },
  "locators": [...],
  "ai_enrichment": {...}  // if --gemini used
}
```

Each locator entry includes:
- `custom_name`: Human-readable element name
- `locator_type`: CSS Selector, XPath, Role Selector, etc.
- `locator_value`: The actual locator string
- `stability`: High/Medium/Low
- `stability_score`: 1-10 numeric score
- `automation_tool`: Playwright/Selenium/Both
- `playwright_code`: Ready-to-use Playwright snippet
- `selenium_code`: Ready-to-use Selenium snippet
- `validated`: true/false (if --validate used)
- `match_count`: Number of elements matched (if validated)
- `dynamic`: true/false (detected dynamic attributes)
- `duplicate`: true/false (duplicate IDs/names)
- `warnings`: Array of warnings

## Authenticated Validation (Playwright)

Option A: Use storage state
```bash
python smart_locator_ai.py \
  --url https://your.app/page \
  --validate \
  --auth-storage-state path/to/storage_state.json
```

Option B: Scripted login
```bash
python smart_locator_ai.py \
  --url https://your.app/protected \
  --validate \
  --auth-url https://your.app/login \
  --auth-user USER --auth-pass PASS \
  --user-selector "#username" \
  --pass-selector "#password" \
  --submit-selector "button[type='submit']" \
  --auth-wait-selector "a.main-menu"
```

Notes:
- Validates each locator; adds `validated`, `match_count`, and `validation_error` fields.
- Works for URL inputs; validation is skipped for raw HTML.

## Programmatic Usage

```python
from smart_locator_ai import SmartLocatorAI

runner = SmartLocatorAI()
paths = runner.run(
    html_or_url="https://example.com",
    framework="both",
    min_stability="Medium",
    use_js=False,
    class_name="ProductPage",
    validate=False,
)
print(paths)
```

## CLI Reference

```bash
python smart_locator_ai.py --help
```
Key flags:
- Input: `--url | --file | --html`
- Framework: `--framework both|playwright|selenium`
- Filter: `--min-stability High|Medium|Low`
- JS render: `--js`
- Class name: `--class-name ProductPage`
- Validation: `--validate`
- Auth (optional): `--auth-storage-state`, or scripted login with `--auth-url --auth-user --auth-pass --user-selector --pass-selector --submit-selector --auth-wait-selector|--auth-wait-url-contains`

## Minimal Project Files

- `smart_locator_ai.py` (orchestrates end-to-end)
- `dom_scanner.py` (scan, locator generation, reporting helpers)
- `page_object_exporter.py` (POM generation)
- `requirements.txt`
- `exports/` (generated outputs)

Legacy/demo files (Gemini, demos) are not required for Smart Locator AI pipeline.

## License

MIT (see `LICENSE`).
