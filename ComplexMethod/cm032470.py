def open_upload_modal_from_dataset_detail(page, expect, auth_click, timeout_ms: int):
    """Open the upload modal from dataset detail view."""
    wait_for_dataset_detail_ready(page, expect, timeout_ms=timeout_ms)
    page.wait_for_selector("button", timeout=timeout_ms)

    if hasattr(page, "get_by_role"):
        tab_locator = page.get_by_role(
            "tab", name=re.compile(r"^(files|documents|file)$", re.I)
        )
        if tab_locator.count() > 0:
            tab = tab_locator.first
            try:
                if tab.is_visible():
                    tab.click()
                    page.wait_for_timeout(250)
            except Exception:
                pass

    candidate_names = re.compile(
        r"(upload file|upload|add file|add document|add|new)", re.I
    )
    trigger_locator = None
    if hasattr(page, "get_by_role"):
        trigger_locator = page.get_by_role("button", name=candidate_names)
    if trigger_locator is None or trigger_locator.count() == 0:
        trigger_locator = page.locator("[role='button'], button, a").filter(
            has_text=candidate_names
        )

    trigger = None
    if trigger_locator.count() > 0:
        limit = min(trigger_locator.count(), 5)
        for idx in range(limit):
            candidate = trigger_locator.nth(idx)
            try:
                if candidate.is_visible():
                    trigger = candidate
                    break
            except Exception:
                continue

    if trigger is None:
        aria_candidates = page.locator(
            "button[aria-label], button[title], [role='button'][aria-label], [role='button'][title]"
        )
        limit = min(aria_candidates.count(), 10)
        for idx in range(limit):
            candidate = aria_candidates.nth(idx)
            try:
                if not candidate.is_visible():
                    continue
                aria_label = candidate.get_attribute("aria-label") or ""
                title = candidate.get_attribute("title") or ""
                if candidate_names.search(aria_label) or candidate_names.search(title):
                    trigger = candidate
                    break
            except Exception:
                continue

    if trigger is None:
        if env_bool("PW_DEBUG_DUMP"):
            debug("[dataset] upload_trigger_not_found initial scan")
        button_dump = []
        buttons = page.locator("button")
        total = buttons.count()
        limit = min(total, 20)
        for idx in range(limit):
            item = buttons.nth(idx)
            try:
                if not item.is_visible():
                    continue
            except Exception:
                continue
            try:
                text = item.inner_text().strip()
            except Exception as exc:
                text = f"<text-error:{exc}>"
            try:
                aria_label = item.get_attribute("aria-label")
            except Exception as exc:
                aria_label = f"<aria-error:{exc}>"
            try:
                title = item.get_attribute("title")
            except Exception as exc:
                title = f"<title-error:{exc}>"
            button_dump.append(
                {"text": text, "aria_label": aria_label, "title": title}
            )
        raise AssertionError(
            "Upload entrypoint not found on dataset detail page. "
            f"visible_buttons={button_dump}"
        )

    try:
        if trigger.evaluate("el => el.tagName.toLowerCase() === 'button'"):
            auth_click(trigger, "open_upload")
        else:
            trigger.click()
    except Exception:
        trigger.click()

    def _click_upload_file_popover_item() -> bool:
        locators = [
            page.locator("[role='menuitem']").filter(
                has_text=re.compile(r"^upload file$", re.I)
            ),
            page.locator("[role='option']").filter(
                has_text=re.compile(r"^upload file$", re.I)
            ),
            page.locator("div, span, li").filter(
                has_text=re.compile(r"^upload file$", re.I)
            ),
        ]
        for locator in locators:
            if locator.count() == 0:
                continue
            limit = min(locator.count(), 5)
            for idx in range(limit):
                candidate = locator.nth(idx)
                try:
                    if candidate.is_visible():
                        candidate.click()
                        return True
                except Exception:
                    continue
        return False

    clicked_item = _click_upload_file_popover_item()
    if not clicked_item:
        if env_bool("PW_DEBUG_DUMP"):
            try:
                button_texts = page.evaluate(
                    """
                    () => Array.from(document.querySelectorAll('button,[role="button"],a'))
                      .filter((el) => {
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                      })
                      .map((el) => (el.innerText || '').trim())
                      .filter(Boolean)
                      .slice(0, 20)
                    """
                )
            except Exception:
                button_texts = []
            has_upload_text = page.locator("text=/upload file/i").count() > 0
            debug(f"[dataset] upload_item_missing has_upload_text={has_upload_text}")
            debug(f"[dataset] visible_button_texts={button_texts}")
        raise AssertionError(
            "Upload file popover item not found after clicking Add trigger."
        )

    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    except Exception:
        pass

    upload_modal = page.locator("[data-testid='dataset-upload-modal']")
    expect(upload_modal).to_be_visible(timeout=timeout_ms)
    return upload_modal