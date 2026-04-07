def test_no_urls_exception(self):
        """
        URLResolver should raise an exception when no urlpatterns exist.
        """
        resolver = URLResolver(RegexPattern(r"^$"), settings.ROOT_URLCONF)

        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "The included URLconf 'urlpatterns_reverse.no_urls' does not "
            "appear to have any patterns in it. If you see the 'urlpatterns' "
            "variable with valid patterns in the file then the issue is "
            "probably caused by a circular import.",
        ):
            getattr(resolver, "url_patterns")