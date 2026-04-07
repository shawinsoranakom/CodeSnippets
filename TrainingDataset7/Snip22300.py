def setUp(self):
        # Site fields cache needs to be cleared after flatpages is added to
        # INSTALLED_APPS
        Site._meta._expire_cache()
        self.form_data = {
            "title": "A test page",
            "content": "This is a test",
            "sites": [settings.SITE_ID],
        }