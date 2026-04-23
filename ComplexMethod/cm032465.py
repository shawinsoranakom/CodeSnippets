def _open_create_from_list(
    page,
    empty_testid: str,
    create_btn_testid: str,
    modal_testid: str = "rename-modal",
):
    empty = page.locator(f"[data-testid='{empty_testid}']")
    if empty.count() > 0 and empty.first.is_visible():
        empty.first.click()
    else:
        create_btn = page.locator(f"[data-testid='{create_btn_testid}']")
        if create_btn.count() > 0:
            expect(create_btn.first).to_be_visible(timeout=RESULT_TIMEOUT_MS)
            create_btn.first.click()
        else:
            create_text_map = {
                "create-chat": r"create\s+chat",
                "create-search": r"create\s+search",
                "create-agent": r"create\s+agent",
            }
            pattern = create_text_map.get(create_btn_testid)
            clicked = False
            if pattern:
                fallback_btn = page.get_by_role(
                    "button", name=re.compile(pattern, re.I)
                )
                if fallback_btn.count() > 0 and fallback_btn.first.is_visible():
                    fallback_btn.first.click()
                    clicked = True

            if not clicked:
                empty_text_map = {
                    "chats-empty-create": r"no chat app created yet",
                    "search-empty-create": r"no search app created yet",
                    "agents-empty-create": r"no agent",
                }
                empty_pattern = empty_text_map.get(empty_testid)
                if empty_pattern:
                    empty_state = page.locator("div, section, article").filter(
                        has_text=re.compile(empty_pattern, re.I)
                    )
                    if empty_state.count() > 0 and empty_state.first.is_visible():
                        empty_state.first.click()
                        clicked = True

            if not clicked:
                fallback_card = page.locator(
                    ".border-dashed, [class*='border-dashed']"
                ).first
                expect(fallback_card).to_be_visible(timeout=RESULT_TIMEOUT_MS)
                fallback_card.click()
    if modal_testid == "agent-create-modal":
        menu = page.locator("[data-testid='agent-create-menu']")
        if menu.count() > 0 and menu.first.is_visible():
            create_blank = menu.locator("text=/create from blank/i")
            if create_blank.count() > 0 and create_blank.first.is_visible():
                create_blank.first.click()
            else:
                first_item = menu.locator("[role='menuitem']").first
                expect(first_item).to_be_visible(timeout=RESULT_TIMEOUT_MS)
                first_item.click()
    modal = page.locator(f"[data-testid='{modal_testid}']")
    expect(modal).to_be_visible(timeout=RESULT_TIMEOUT_MS)
    return modal