def setUp(self):
        urlconf = "urlpatterns_reverse.urls_error_handlers"
        urlconf_callables = "urlpatterns_reverse.urls_error_handlers_callables"
        self.resolver = URLResolver(RegexPattern(r"^$"), urlconf)
        self.callable_resolver = URLResolver(RegexPattern(r"^$"), urlconf_callables)