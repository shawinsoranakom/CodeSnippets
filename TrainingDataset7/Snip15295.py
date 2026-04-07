def setUp(self):
        # Reset admin.site since it may have already been instantiated by
        # another test app.
        self._old_site = admin.site
        admin.site = sites.site = sites.DefaultAdminSite()