def reverse(
    viewname,
    urlconf=None,
    args=None,
    kwargs=None,
    current_app=None,
    *,
    query=None,
    fragment=None,
):
    if urlconf is None:
        urlconf = get_urlconf()
    resolver = get_resolver(urlconf)
    args = args or []
    kwargs = kwargs or {}

    prefix = get_script_prefix()

    if not isinstance(viewname, str):
        view = viewname
    else:
        *path, view = viewname.split(":")

        if current_app:
            current_path = current_app.split(":")
            current_path.reverse()
        else:
            current_path = None

        resolved_path = []
        ns_pattern = ""
        ns_converters = {}
        for ns in path:
            current_ns = current_path.pop() if current_path else None
            # Lookup the name to see if it could be an app identifier.
            try:
                app_list = resolver.app_dict[ns]
                # Yes! Path part matches an app in the current Resolver.
                if current_ns and current_ns in app_list:
                    # If we are reversing for a particular app, use that
                    # namespace.
                    ns = current_ns
                elif ns not in app_list:
                    # The name isn't shared by one of the instances (i.e.,
                    # the default) so pick the first instance as the default.
                    ns = app_list[0]
            except KeyError:
                pass

            if ns != current_ns:
                current_path = None

            try:
                extra, resolver = resolver.namespace_dict[ns]
                resolved_path.append(ns)
                ns_pattern += extra
                ns_converters.update(resolver.pattern.converters)
            except KeyError as key:
                if resolved_path:
                    raise NoReverseMatch(
                        "%s is not a registered namespace inside '%s'"
                        % (key, ":".join(resolved_path))
                    )
                else:
                    raise NoReverseMatch("%s is not a registered namespace" % key)
        if ns_pattern:
            resolver = get_ns_resolver(
                ns_pattern, resolver, tuple(ns_converters.items())
            )

    resolved_url = resolver._reverse_with_prefix(view, prefix, *args, **kwargs)
    if query is not None:
        if isinstance(query, QueryDict):
            query_string = query.urlencode()
        else:
            query_string = urlencode(query, doseq=True)
        if query_string:
            resolved_url += "?" + query_string
    if fragment is not None:
        resolved_url += "#" + fragment
    return resolved_url