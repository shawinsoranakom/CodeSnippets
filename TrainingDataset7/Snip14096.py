def _populate(self):
        # Short-circuit if called recursively in this thread to prevent
        # infinite recursion. Concurrent threads may call this at the same
        # time and will need to continue, so set 'populating' on a
        # thread-local variable.
        if getattr(self._local, "populating", False):
            return
        try:
            self._local.populating = True
            lookups = MultiValueDict()
            namespaces = {}
            apps = {}
            language_code = get_language()
            for url_pattern in reversed(self.url_patterns):
                p_pattern = url_pattern.pattern.regex.pattern
                p_pattern = p_pattern.removeprefix("^")
                if isinstance(url_pattern, URLPattern):
                    self._callback_strs.add(url_pattern.lookup_str)
                    bits = normalize(url_pattern.pattern.regex.pattern)
                    lookups.appendlist(
                        url_pattern.callback,
                        (
                            bits,
                            p_pattern,
                            url_pattern.default_args,
                            url_pattern.pattern.converters,
                        ),
                    )
                    if url_pattern.name is not None:
                        lookups.appendlist(
                            url_pattern.name,
                            (
                                bits,
                                p_pattern,
                                url_pattern.default_args,
                                url_pattern.pattern.converters,
                            ),
                        )
                else:  # url_pattern is a URLResolver.
                    url_pattern._populate()
                    if url_pattern.app_name:
                        apps.setdefault(url_pattern.app_name, []).append(
                            url_pattern.namespace
                        )
                        namespaces[url_pattern.namespace] = (p_pattern, url_pattern)
                    else:
                        for name in url_pattern.reverse_dict:
                            for (
                                matches,
                                pat,
                                defaults,
                                converters,
                            ) in url_pattern.reverse_dict.getlist(name):
                                new_matches = normalize(p_pattern + pat)
                                lookups.appendlist(
                                    name,
                                    (
                                        new_matches,
                                        p_pattern + pat,
                                        {**defaults, **url_pattern.default_kwargs},
                                        {
                                            **self.pattern.converters,
                                            **url_pattern.pattern.converters,
                                            **converters,
                                        },
                                    ),
                                )
                        for namespace, (
                            prefix,
                            sub_pattern,
                        ) in url_pattern.namespace_dict.items():
                            current_converters = url_pattern.pattern.converters
                            sub_pattern.pattern.converters.update(current_converters)
                            namespaces[namespace] = (p_pattern + prefix, sub_pattern)
                        for app_name, namespace_list in url_pattern.app_dict.items():
                            apps.setdefault(app_name, []).extend(namespace_list)
                    self._callback_strs.update(url_pattern._callback_strs)
            self._namespace_dict[language_code] = namespaces
            self._app_dict[language_code] = apps
            self._reverse_dict[language_code] = lookups
            self._populated = True
        finally:
            self._local.populating = False