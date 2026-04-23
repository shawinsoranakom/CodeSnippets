def test_install_app_no_warning(self):
        # Clear cache to force queries when (re)initializing the
        # "django.contrib.postgres" app.
        get_hstore_oids.cache_clear()
        with CaptureQueriesContext(connection) as captured_queries:
            with override_settings(INSTALLED_APPS=["django.contrib.postgres"]):
                pass
        self.assertGreaterEqual(len(captured_queries), 1)