def _test_project_locale_paths(self, locale_path):
        """
        * translations for an app containing a locale folder are stored in that
          folder
        * translations outside of that app are in LOCALE_PATHS[0]
        """
        with override_settings(LOCALE_PATHS=[locale_path]):
            management.call_command("makemessages", locale=[LOCALE], verbosity=0)
            project_de_locale = os.path.join(
                self.test_dir, "project_locale", "de", "LC_MESSAGES", "django.po"
            )
            app_de_locale = os.path.join(
                self.test_dir,
                "app_with_locale",
                "locale",
                "de",
                "LC_MESSAGES",
                "django.po",
            )
            self.assertTrue(os.path.exists(project_de_locale))
            self.assertTrue(os.path.exists(app_de_locale))

            with open(project_de_locale) as fp:
                po_contents = fp.read()
                self.assertMsgId("This app has no locale directory", po_contents)
                self.assertMsgId("This is a project-level string", po_contents)
            with open(app_de_locale) as fp:
                po_contents = fp.read()
                self.assertMsgId("This app has a locale directory", po_contents)