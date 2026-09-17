from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from app.core.config import settings

_persistent_context: BrowserContext | None = None
_playwright_instance: Playwright | None = None
_browser: Browser | None = None

APPLY_BUTTON_SELECTORS = [
    "button:has-text('Easy Apply')",
    "button:has-text('Apply')",
    "button:has-text('Submit application')",
    "[data-automation='apply-button']",
    "button[aria-label*='Apply']",
    "a:has-text('Apply')",
    "a:has-text('Easy Apply')",
    "button:has-text('Quick Apply')",
    "a:has-text('Quick Apply')",
    "button:has-text('Submit')",
    "button[type='submit']",
]

FILL_SELECTORS_BY_FIELD = {
    "email": [
        "input[name='email']",
        "input[autocomplete='email']",
        "input[type='email']",
        "input[name*='email']",
    ],
    "phone": [
        "input[name='phoneNumber']",
        "input[name='phone']",
        "input[name*='phone']",
        "input[type='tel']",
    ],
    "name": [
        "input[name='firstName']",
        "input[aria-label='First name']",
        "input[name*='first']",
    ],
    "last_name": [
        "input[name='lastName']",
        "input[aria-label='Last name']",
        "input[name*='last']",
    ],
}


async def _get_context() -> BrowserContext:
    global _persistent_context, _playwright_instance, _browser
    if _persistent_context is not None:
        return _persistent_context
    _playwright_instance = await async_playwright().start()
    _browser = await _playwright_instance.chromium.launch(
        headless=settings.browser_headless,
        args=["--disable-blink-features=AutomationControlled"],
    )
    _persistent_context = await _browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        storage_state=str(settings.data_dir / "browser_auth_state.json") if (settings.data_dir / "browser_auth_state.json").exists() else None,
    )
    return _persistent_context


async def save_browser_state() -> None:
    context = await _get_context()
    state_dir = settings.data_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    await context.storage_state(path=str(state_dir / "browser_auth_state.json"))


async def login_interactive(platform: str) -> str:
    context = await _get_context()
    page = await context.new_page()
    if platform == "linkedin":
        await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
    elif platform == "indeed":
        await page.goto("https://secure.indeed.com/auth", wait_until="domcontentloaded")
    else:
        return "Unknown platform"
    await page.wait_for_timeout(500)
    prompt = (
        "A browser window is open. Log in manually, then come back and run finish_login.\n"
        "Waiting..."
    )
    await page.wait_for_timeout(3000)
    current_url = page.url
    return prompt + f"\nCurrently at: {current_url}"


async def finish_login() -> str:
    context = await _get_context()
    pages = context.pages
    if not pages:
        return "No browser pages are open."
    await pages[0].wait_for_timeout(1000)
    await save_browser_state()
    return f"Saved login state from {pages[0].url}"


async def extract_job_details(url: str) -> dict[str, str]:
    context = await _get_context()
    page = await context.new_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    result: dict[str, str] = {"url": url, "title": "", "company": "", "description": "", "error": ""}

    try:
        selectors = [
            "h1",
            "[data-automation='jobTitle']",
            "h1.jobsearch-JobInfoHeader-title",
            ".top-card-layout__headline",
            ".top-card-layout__title",
        ]
        for sel in selectors:
            el = await page.query_selector(sel)
            if el:
                result["title"] = (await el.text_content() or "").strip()
                break

        company_selectors = [
            "[data-automation='jobCompanyLink']",
            ".top-card-layout__second-link",
            "a.topcard__org-name-link",
            ".jobsearch-CompanyInfoWithoutHeaderImage a",
            ".company_name",
        ]
        for sel in company_selectors:
            el = await page.query_selector(sel)
            if el:
                result["company"] = (await el.text_content() or "").strip()
                break

        desc_selectors = [
            "[data-automation='jobDescriptionText']",
            ".description__text",
            "#jobDescriptionText",
            ".jobsearch-jobDescriptionText",
        ]
        for sel in desc_selectors:
            el = await page.query_selector(sel)
            if el:
                result["description"] = (await el.text_content() or "").strip()[:3000]
                break
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        await page.close()
    return result


async def fill_and_submit_application(url: str, profile_data: dict[str, str], answers: dict[str, str], approval_required: bool = True) -> dict[str, str]:
    context = await _get_context()
    page = await context.new_page()
    result: dict[str, str] = {"url": url, "status": "unknown", "message": "", "error": ""}

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        linkedin_login_markers = ["linkedin.com/login", "linkedin.com/authwall"]
        if any(marker in page.url for marker in linkedin_login_markers):
            result["status"] = "needs_login"
            result["error"] = "Not logged into this platform. Run login_interactive first."
            await page.close()
            return result

        all_values = {**profile_data, **answers}

        for field_key, selectors in FILL_SELECTORS_BY_FIELD.items():
            value_to_fill = all_values.get(field_key, "")
            if not value_to_fill:
                continue
            for sel in selectors:
                elements = await page.query_selector_all(sel)
                for el in elements:
                    try:
                        await el.fill(value_to_fill)
                    except Exception:
                        try:
                            await el.type(value_to_fill, delay=30)
                        except Exception:
                            pass
                        break
                if elements:
                    break

        for sel in APPLY_BUTTON_SELECTORS:
            button = await page.query_selector(sel)
            if button:
                is_visible = await button.is_visible()
                is_enabled = await button.is_enabled()
                if is_visible and is_enabled:
                    if approval_required:
                        result["status"] = "needs_approval"
                        result["message"] = f"Ready to apply at {page.url}. Approve the submit."
                        await save_browser_state()
                        await page.close()
                        return result
                    await button.click()
                    await page.wait_for_timeout(3000)
                    result["status"] = "submitted"
                    result["message"] = "Clicked apply button."
                    await save_browser_state()
                    await page.close()
                    return result

        result["status"] = "could_not_find_apply_button"
        result["error"] = "No apply button was found on the page."
    except Exception as exc:
        result["status"] = "error"
        result["error"] = str(exc)
    finally:
        try:
            await save_browser_state()
        except Exception:
            pass
    try:
        await page.close()
    except Exception:
        pass
    return result


async def navigate_current_page() -> dict[str, str]:
    context = await _get_context()
    pages = context.pages
    if not pages:
        return {"url": "", "title": "", "content_preview": ""}
    page = pages[-1]
    content = await page.content()
    return {
        "url": page.url,
        "title": await page.title(),
        "content_preview": content[:4000],
    }