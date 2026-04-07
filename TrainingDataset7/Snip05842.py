def _setup(self):
        AdminSiteClass = import_string(apps.get_app_config("admin").default_site)
        self._wrapped = AdminSiteClass()