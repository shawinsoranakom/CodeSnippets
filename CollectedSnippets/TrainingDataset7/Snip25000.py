def test_i18n_catalog_ignored_when_invoked_for_django(self):
        # Create target file so it exists in the filesystem and can be ignored.
        # "invoked_for_django" is True when "conf/locale" folder exists.
        os.makedirs(os.path.join("conf", "locale"))
        i18n_catalog_js_dir = os.path.join(os.path.curdir, "views", "templates")
        os.makedirs(i18n_catalog_js_dir)
        open(os.path.join(i18n_catalog_js_dir, "i18n_catalog.js"), "w").close()

        out, _ = self._run_makemessages(domain="djangojs")
        self.assertIn(f"ignoring file i18n_catalog.js in {i18n_catalog_js_dir}", out)