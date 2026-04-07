def get_context_data(self, **kwargs):
        views = []
        url_resolver = get_resolver(get_urlconf())
        try:
            view_functions = extract_views_from_urlpatterns(url_resolver.url_patterns)
        except ImproperlyConfigured:
            view_functions = []
        for func, regex, namespace, name in view_functions:
            views.append(
                {
                    "full_name": get_view_name(func),
                    "url": simplify_regex(regex),
                    "url_name": ":".join((namespace or []) + (name and [name] or [])),
                    "namespace": ":".join(namespace or []),
                    "name": name,
                }
            )
        return super().get_context_data(**{**kwargs, "views": views})