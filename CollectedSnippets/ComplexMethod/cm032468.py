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