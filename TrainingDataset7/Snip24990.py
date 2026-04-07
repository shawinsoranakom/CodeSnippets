def test_makemessages_find_files(self):
        """
        find_files only discover files having the proper extensions.
        """
        cmd = MakeMessagesCommand()
        cmd.ignore_patterns = ["CVS", ".*", "*~", "*.pyc"]
        cmd.symlinks = False
        cmd.domain = "django"
        cmd.extensions = [".html", ".txt", ".py"]
        cmd.verbosity = 0
        cmd.locale_paths = []
        cmd.default_locale_path = os.path.join(self.test_dir, "locale")
        found_files = cmd.find_files(self.test_dir)
        self.assertGreater(len(found_files), 1)
        found_exts = {os.path.splitext(tfile.file)[1] for tfile in found_files}
        self.assertEqual(found_exts.difference({".py", ".html", ".txt"}), set())

        cmd.extensions = [".js"]
        cmd.domain = "djangojs"
        found_files = cmd.find_files(self.test_dir)
        self.assertGreater(len(found_files), 1)
        found_exts = {os.path.splitext(tfile.file)[1] for tfile in found_files}
        self.assertEqual(found_exts.difference({".js"}), set())