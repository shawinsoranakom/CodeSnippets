def test_all_locales(self):
        """
        When the `locale` flag is absent, all dirs from the parent locale dir
        are considered as language directories, except if the directory doesn't
        start with two letters (which excludes __pycache__, .gitignore, etc.).
        """
        os.mkdir(os.path.join("locale", "_do_not_pick"))
        # Excluding locales that do not compile
        management.call_command("makemessages", exclude=["ja", "es_AR"], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE_KO))
        self.assertFalse(os.path.exists("locale/_do_not_pick/LC_MESSAGES/django.po"))