def set_page_config(
    page_title: Optional[str] = None,
    page_icon: Optional[PageIcon] = None,
    layout: Layout = "centered",
    initial_sidebar_state: InitialSideBarState = "auto",
    menu_items: Optional[MenuItems] = None,
) -> None:
    """
    Configures the default settings of the page.

    .. note::
        This must be the first Streamlit command used in your app, and must only
        be set once.

    Parameters
    ----------
    page_title: str or None
        The page title, shown in the browser tab. If None, defaults to the
        filename of the script ("app.py" would show "app • Streamlit").
    page_icon : Anything supported by st.image or str or None
        The page favicon.
        Besides the types supported by `st.image` (like URLs or numpy arrays),
        you can pass in an emoji as a string ("🦈") or a shortcode (":shark:").
        If you're feeling lucky, try "random" for a random emoji!
        Emoji icons are courtesy of Twemoji and loaded from MaxCDN.
    layout: "centered" or "wide"
        How the page content should be laid out. Defaults to "centered",
        which constrains the elements into a centered column of fixed width;
        "wide" uses the entire screen.
    initial_sidebar_state: "auto" or "expanded" or "collapsed"
        How the sidebar should start out. Defaults to "auto",
        which hides the sidebar on mobile-sized devices, and shows it otherwise.
        "expanded" shows the sidebar initially; "collapsed" hides it.
    menu_items: dict
        Configure the menu that appears on the top-right side of this app.
        The keys in this dict denote the menu item you'd like to configure:

        - "Get help": str or None
            The URL this menu item should point to.
            If None, hides this menu item.
        - "Report a Bug": str or None
            The URL this menu item should point to.
            If None, hides this menu item.
        - "About": str or None
            A markdown string to show in the About dialog.
            If None, only shows Streamlit's default About text.

        The URL may also refer to an email address e.g. ``mailto:john@example.com``.

    Example
    -------
    >>> st.set_page_config(
    ...     page_title="Ex-stream-ly Cool App",
    ...     page_icon="🧊",
    ...     layout="wide",
    ...     initial_sidebar_state="expanded",
    ...     menu_items={
    ...         'Get Help': 'https://www.extremelycoolapp.com/help',
    ...         'Report a bug': "https://www.extremelycoolapp.com/bug",
    ...         'About': "# This is a header. This is an *extremely* cool app!"
    ...     }
    ... )
    """

    msg = ForwardProto()

    if page_title is not None:
        msg.page_config_changed.title = page_title

    if page_icon is not None:
        msg.page_config_changed.favicon = _get_favicon_string(page_icon)

    pb_layout: "PageConfigProto.Layout.ValueType"
    if layout == "centered":
        pb_layout = PageConfigProto.CENTERED
    elif layout == "wide":
        pb_layout = PageConfigProto.WIDE
    else:
        raise StreamlitAPIException(
            f'`layout` must be "centered" or "wide" (got "{layout}")'
        )
    msg.page_config_changed.layout = pb_layout

    pb_sidebar_state: "PageConfigProto.SidebarState.ValueType"
    if initial_sidebar_state == "auto":
        pb_sidebar_state = PageConfigProto.AUTO
    elif initial_sidebar_state == "expanded":
        pb_sidebar_state = PageConfigProto.EXPANDED
    elif initial_sidebar_state == "collapsed":
        pb_sidebar_state = PageConfigProto.COLLAPSED
    else:
        raise StreamlitAPIException(
            "`initial_sidebar_state` must be "
            '"auto" or "expanded" or "collapsed" '
            f'(got "{initial_sidebar_state}")'
        )

    msg.page_config_changed.initial_sidebar_state = pb_sidebar_state

    if menu_items is not None:
        lowercase_menu_items = cast(MenuItems, lower_clean_dict_keys(menu_items))
        validate_menu_items(lowercase_menu_items)
        menu_items_proto = msg.page_config_changed.menu_items
        set_menu_items_proto(lowercase_menu_items, menu_items_proto)

    ctx = get_script_run_ctx()
    if ctx is None:
        return
    ctx.enqueue(msg)