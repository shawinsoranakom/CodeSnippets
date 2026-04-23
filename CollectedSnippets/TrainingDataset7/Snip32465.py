def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir)

        # get modification and access times for no_label/static/file2.txt
        self.orig_path = os.path.join(
            TEST_ROOT, "apps", "no_label", "static", "file2.txt"
        )
        self.orig_mtime = os.path.getmtime(self.orig_path)
        self.orig_atime = os.path.getatime(self.orig_path)

        # prepare duplicate of file2.txt from a temporary app
        # this file will have modification time older than
        # no_label/static/file2.txt anyway it should be taken to STATIC_ROOT
        # because the temporary app is before 'no_label' app in installed apps
        self.temp_app_path = os.path.join(self.temp_dir, "staticfiles_test_app")
        self.testfile_path = os.path.join(self.temp_app_path, "static", "file2.txt")

        os.makedirs(self.temp_app_path)
        with open(os.path.join(self.temp_app_path, "__init__.py"), "w+"):
            pass

        os.makedirs(os.path.dirname(self.testfile_path))
        with open(self.testfile_path, "w+") as f:
            f.write("duplicate of file2.txt")

        os.utime(self.testfile_path, (self.orig_atime - 1, self.orig_mtime - 1))

        settings_with_test_app = self.modify_settings(
            INSTALLED_APPS={"prepend": "staticfiles_test_app"},
        )
        with extend_sys_path(self.temp_dir):
            settings_with_test_app.enable()
        self.addCleanup(settings_with_test_app.disable)
        super().setUp()