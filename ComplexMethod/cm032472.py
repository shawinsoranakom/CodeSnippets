def _click_create_button_entrypoint() -> None:
        debug("[dataset] using create button entrypoint")
        create_btn = None
        if hasattr(page, "get_by_role"):
            create_btn = page.get_by_role("button", name=re.compile(r"create dataset", re.I))
        if create_btn is None or create_btn.count() == 0:
            create_btn = page.locator(
                "button", has_text=re.compile(r"create dataset", re.I)
            ).first
        if create_btn.count() == 0:
            if env_bool("PW_DEBUG_DUMP"):
                url = page.url
                body_text = page.evaluate(
                    "(() => (document.body && document.body.innerText) || '')()"
                )
                lines = body_text.splitlines()
                snippet = "\n".join(lines[:20])[:500]
                debug(f"[dataset] entrypoint_not_found url={url} snippet={snippet!r}")
                dump_clickable_candidates(page)
            raise AssertionError("No dataset entrypoint found after readiness wait.")
        debug(f"[dataset] create_button_count={create_btn.count()}")
        try:
            expect(create_btn).to_be_visible(timeout=5000)
        except AssertionError:
            if env_bool("PW_DEBUG_DUMP"):
                url = page.url
                body_text = page.evaluate(
                    "(() => (document.body && document.body.innerText) || '')()"
                )
                lines = body_text.splitlines()
                snippet = "\n".join(lines[:20])[:500]
                debug(f"[dataset] entrypoint_not_found url={url} snippet={snippet!r}")
            raise
        _click_entrypoint(create_btn)