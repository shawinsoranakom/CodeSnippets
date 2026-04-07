def get_script_name(environ):
    """
    Return the equivalent of the HTTP request's SCRIPT_NAME environment
    variable. If Apache mod_rewrite is used, return what would have been
    the script name prior to any rewriting (so it's the script name as seen
    from the client's perspective), unless the FORCE_SCRIPT_NAME setting is
    set (to anything).
    """
    if settings.FORCE_SCRIPT_NAME is not None:
        return settings.FORCE_SCRIPT_NAME

    # If Apache's mod_rewrite had a whack at the URL, Apache set either
    # SCRIPT_URL or REDIRECT_URL to the full resource URL before applying any
    # rewrites. Unfortunately not every web server (lighttpd!) passes this
    # information through all the time, so FORCE_SCRIPT_NAME, above, is still
    # needed.
    script_url = get_bytes_from_wsgi(environ, "SCRIPT_URL", "") or get_bytes_from_wsgi(
        environ, "REDIRECT_URL", ""
    )

    if script_url:
        if b"//" in script_url:
            # mod_wsgi squashes multiple successive slashes in PATH_INFO,
            # do the same with script_url before manipulating paths (#17133).
            script_url = _slashes_re.sub(b"/", script_url)
        path_info = get_bytes_from_wsgi(environ, "PATH_INFO", "")
        script_name = script_url.removesuffix(path_info)
    else:
        script_name = get_bytes_from_wsgi(environ, "SCRIPT_NAME", "")

    return script_name.decode()