def tearDown(self):
        admin.site = sites.site = self._old_site