def validate_menu_items(menu_items: MenuItems) -> None:
    for k, v in menu_items.items():
        if not valid_menu_item_key(k):
            raise StreamlitAPIException(
                "We only accept the keys: "
                '"Get help", "Report a bug", and "About" '
                f'("{k}" is not a valid key.)'
            )
        if v is not None:
            if not valid_url(v) and k != ABOUT_KEY:
                raise StreamlitAPIException(f'"{v}" is a not a valid URL!')