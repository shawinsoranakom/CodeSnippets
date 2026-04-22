def user_key_from_widget_id(wid: str) -> Optional[str]:
    """Extract the user key used to generate a widget id, from that id.

    Returns `None` instead of `"None"` if there was no user key,
    for compatibility with the rest of the codebase, which represents it that way.

    TODO This will incorrectly indicate no user key if the user actually provides
    "None" as a key, but we can't avoid this kind of problem while storing the
    string representation of the no-user-key sentinel as part of the widget id.
    """
    user_key = wid.split("-", maxsplit=2)[-1]
    user_key = None if user_key == "None" else user_key
    return user_key