def test_i18n_catalog_not_ignored_when_not_invoked_for_django(self):
        # Create target file so it exists in the filesystem but is NOT ignored.
        # "invoked_for_django" is False when "conf/locale" folder does not
        # exist.
        self.assertIs(os.path.exists(os.path.join("conf", "locale")), False)
        i18n_catalog_js = os.path.join("views", "templates", "i18n_catalog.js")
        os.makedirs(os.path.dirname(i18n_catalog_js))
        open(i18n_catalog_js, "w").close()

        out, _ = self._run_makemessages(domain="djangojs")
        self.assertNotIn("ignoring file i18n_catalog.js", out)