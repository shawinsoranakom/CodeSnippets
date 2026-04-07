def test_resolver_cache_default__root_urlconf(self):
        # resolver for a default URLconf (passing no argument) and for the
        # settings.ROOT_URLCONF is the same cached object.
        self.assertIs(get_resolver(), get_resolver("urlpatterns.path_urls"))
        self.assertIsNot(get_resolver(), get_resolver("urlpatterns.path_dynamic_urls"))