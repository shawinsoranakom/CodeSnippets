def _select_first_dataset_and_save(
    page,
    timeout_ms: int = RESULT_TIMEOUT_MS,
    response_timeout_ms: int = 30000,
    post_save_ready_locator=None,
) -> None:
    chat_root = page.locator("[data-testid='chat-detail']")
    search_root = page.locator("[data-testid='search-detail']")
    scope_root = None
    combobox_testid = None
    save_testid = None
    try:
        if chat_root.count() > 0 and chat_root.is_visible():
            scope_root = chat_root
            combobox_testid = "chat-datasets-combobox"
            save_testid = "chat-settings-save"
    except Exception:
        pass
    if scope_root is None:
        try:
            if search_root.count() > 0 and search_root.is_visible():
                scope_root = search_root
                combobox_testid = "search-datasets-combobox"
                save_testid = "search-settings-save"
        except Exception:
            pass
    if scope_root is None:
        scope_root = page
        combobox_testid = "search-datasets-combobox"
        save_testid = "search-settings-save"

    def _find_dataset_combobox(search_scope):
        combo = search_scope.locator(f"[data-testid='{combobox_testid}']")
        if combo.count() > 0:
            return combo
        combo = search_scope.locator("[role='combobox']").filter(
            has_text=re.compile(r"select|dataset|please", re.I)
        )
        if combo.count() > 0:
            return combo
        return search_scope.locator("[role='combobox']")

    combobox = _find_dataset_combobox(scope_root)
    if combobox.count() == 0:
        settings_candidates = [
            scope_root.locator("button:has(svg.lucide-settings)"),
            scope_root.locator("button:has(svg[class*='settings'])"),
            scope_root.locator("[data-testid='chat-settings']"),
            scope_root.locator("[data-testid='search-settings']"),
            scope_root.locator("button", has_text=re.compile(r"search settings", re.I)),
            scope_root.locator("button", has=scope_root.locator("svg.lucide-settings")),
            page.locator("button:has(svg.lucide-settings)"),
            page.locator("button", has_text=re.compile(r"search settings", re.I)),
        ]
        for settings_button in settings_candidates:
            if settings_button.count() == 0:
                continue
            if not settings_button.first.is_visible():
                continue
            settings_button.first.click()
            break

        settings_dialog = page.locator("[role='dialog']").filter(
            has_text=re.compile(r"settings", re.I)
        )
        if settings_dialog.count() > 0 and settings_dialog.first.is_visible():
            scope_root = settings_dialog.first
        combobox = _find_dataset_combobox(scope_root)

    combobox = combobox.first
    expect(combobox).to_be_visible(timeout=timeout_ms)
    combo_text = ""
    try:
        combo_text = combobox.inner_text()
    except Exception:
        combo_text = ""
    if combo_text and not re.search(r"please\s+select|select", combo_text, re.I):
        return

    save_button = scope_root.locator(f"[data-testid='{save_testid}']")
    if save_button.count() == 0:
        save_button = scope_root.get_by_role(
            "button", name=re.compile(r"^save$", re.I)
        )
    if save_button.count() == 0:
        save_button = scope_root.locator(
            "button[type='submit']", has_text=re.compile(r"^save$", re.I)
        ).first
    save_button = save_button.first
    expect(save_button).to_be_visible(timeout=timeout_ms)

    def _open_dataset_options():
        last_list_text = ""
        for _ in range(10):
            candidates = [
                page.locator("[data-testid='datasets-options']:visible"),
                page.locator("[role='listbox']:visible"),
                page.locator("[cmdk-list]:visible"),
            ]
            for candidate in candidates:
                if candidate.count() > 0:
                    options_root = candidate.first
                    expect(options_root).to_be_visible(timeout=timeout_ms)
                    return options_root, last_list_text

            combobox.click()
            page.wait_for_timeout(120)

            list_locator = page.locator("[data-testid='datasets-options']").first
            if list_locator.count() > 0:
                try:
                    last_list_text = list_locator.inner_text() or ""
                except Exception:
                    last_list_text = ""
        raise AssertionError(
            "Dataset option popover did not open. "
            f"combobox_testid={combobox_testid!r} last_list_text={last_list_text[:200]!r}"
        )

    def _pick_first_dataset_option(options_root) -> bool:
        search_input = options_root.locator("[cmdk-input], input[placeholder*='Search']").first
        if search_input.count() > 0:
            try:
                search_input.fill("")
                search_input.focus()
            except Exception:
                pass
            page.wait_for_timeout(100)

        selectors = [
            "[data-testid^='datasets-option-']:not([aria-disabled='true']):not([data-disabled='true'])",
            "[role='option']:not([aria-disabled='true']):not([data-disabled='true'])",
            "[cmdk-item]:not([aria-disabled='true']):not([data-disabled='true'])",
        ]
        for selector in selectors:
            candidates = options_root.locator(selector)
            if candidates.count() == 0:
                continue
            limit = min(candidates.count(), 20)
            for idx in range(limit):
                candidate = candidates.nth(idx)
                try:
                    if not candidate.is_visible():
                        continue
                    text = (candidate.inner_text() or "").strip().lower()
                except Exception:
                    continue
                if (
                    not text
                    or "no results found" in text
                    or text == "close"
                    or text == "clear"
                ):
                    continue
                for _ in range(3):
                    try:
                        candidate.click(timeout=2000)
                        return True
                    except Exception:
                        try:
                            candidate.click(timeout=2000, force=True)
                            return True
                        except Exception:
                            page.wait_for_timeout(100)
                break

        try:
            if search_input.count() > 0:
                search_input.focus()
            else:
                combobox.focus()
            page.keyboard.press("ArrowDown")
            page.keyboard.press("Enter")
            return True
        except Exception:
            return False

    def _parse_request_payload(req) -> dict:
        try:
            payload = req.post_data_json
            if callable(payload):
                payload = payload()
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
        return {}

    def _has_selected_kb_ids(payload: dict) -> bool:
        if save_testid == "search-settings-save":
            search_config = payload.get("search_config", {})
            kb_ids = search_config.get("kb_ids")
            if not isinstance(kb_ids, list):
                kb_ids = payload.get("kb_ids")
            return isinstance(kb_ids, list) and len(kb_ids) > 0
        kb_ids = payload.get("kb_ids")
        return isinstance(kb_ids, list) and len(kb_ids) > 0

    response_url_pattern = (
        "/api/v1/chats" if save_testid == "chat-settings-save" else "/api/v1/searches/"
    )
    last_payload = {}
    last_combobox_text = ""
    last_list_text = ""
    for attempt in range(5):
        options, last_list_text = _open_dataset_options()
        clicked = _pick_first_dataset_option(options)
        if not clicked:
            raise AssertionError(
                "Failed to select dataset option after retries. "
                f"list_text={last_list_text[:200]!r}"
            )

        page.wait_for_timeout(120)
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        response = None
        try:
            response = capture_response(
                page,
                lambda: save_button.click(),
                lambda resp: response_url_pattern in resp.url
                and resp.request.method in ("POST", "PUT", "PATCH"),
                timeout_ms=response_timeout_ms,
            )
        except Exception:
            try:
                save_button.click()
            except Exception:
                pass

        payload = {}
        if response is not None:
            payload = _parse_request_payload(response.request)
        last_payload = payload
        if _has_selected_kb_ids(payload):
            if post_save_ready_locator is not None:
                expect(post_save_ready_locator).to_be_visible(timeout=timeout_ms)
            else:
                page.wait_for_timeout(250)
            return

        try:
            last_combobox_text = (combobox.inner_text() or "").strip()
        except Exception:
            last_combobox_text = ""
        page.wait_for_timeout(200 * (attempt + 1))

    raise AssertionError(
        "Dataset selection did not persist in save payload. "
        f"save_testid={save_testid!r} payload={last_payload!r} "
        f"combobox_text={last_combobox_text!r} list_text={last_list_text[:200]!r}"
    )