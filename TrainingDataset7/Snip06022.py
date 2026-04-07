def get_context_data(self, **kwargs):
        filters = []
        try:
            engine = Engine.get_default()
        except ImproperlyConfigured:
            # Non-trivial TEMPLATES settings aren't supported (#24125).
            pass
        else:
            app_libs = sorted(engine.template_libraries.items())
            builtin_libs = [("", lib) for lib in engine.template_builtins]
            for module_name, library in builtin_libs + app_libs:
                for filter_name, filter_func in library.filters.items():
                    title, body, metadata = utils.parse_docstring(filter_func.__doc__)
                    title = title and utils.parse_rst(
                        title, "filter", _("filter:") + filter_name
                    )
                    body = body and utils.parse_rst(
                        body, "filter", _("filter:") + filter_name
                    )
                    for key in metadata:
                        metadata[key] = utils.parse_rst(
                            metadata[key], "filter", _("filter:") + filter_name
                        )
                    tag_library = module_name.split(".")[-1]
                    filters.append(
                        {
                            "name": filter_name,
                            "title": title,
                            "body": body,
                            "meta": metadata,
                            "library": tag_library,
                        }
                    )
        return super().get_context_data(**{**kwargs, "filters": filters})