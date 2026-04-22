def valid_menu_item_key(key: str) -> "TypeGuard[MenuKey]":
    return key in {GET_HELP_KEY, REPORT_A_BUG_KEY, ABOUT_KEY}