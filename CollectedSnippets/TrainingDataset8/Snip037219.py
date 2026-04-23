def set_menu_items_proto(lowercase_menu_items, menu_items_proto) -> None:
    if GET_HELP_KEY in lowercase_menu_items:
        if lowercase_menu_items[GET_HELP_KEY] is not None:
            menu_items_proto.get_help_url = lowercase_menu_items[GET_HELP_KEY]
        else:
            menu_items_proto.hide_get_help = True

    if REPORT_A_BUG_KEY in lowercase_menu_items:
        if lowercase_menu_items[REPORT_A_BUG_KEY] is not None:
            menu_items_proto.report_a_bug_url = lowercase_menu_items[REPORT_A_BUG_KEY]
        else:
            menu_items_proto.hide_report_a_bug = True

    if ABOUT_KEY in lowercase_menu_items:
        if lowercase_menu_items[ABOUT_KEY] is not None:
            menu_items_proto.about_section_md = dedent(lowercase_menu_items[ABOUT_KEY])