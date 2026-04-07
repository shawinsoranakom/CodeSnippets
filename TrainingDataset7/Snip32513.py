def setUp(self):
        super().setUp()

        temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(temp_dir, "test"))
        self._clear_filename = os.path.join(temp_dir, "test", "cleared.txt")
        with open(self._clear_filename, "w") as f:
            f.write("to be deleted in one test")

        patched_settings = self.settings(
            STATICFILES_DIRS=settings.STATICFILES_DIRS + [temp_dir],
        )
        patched_settings.enable()
        self.addCleanup(patched_settings.disable)
        self.addCleanup(shutil.rmtree, temp_dir)
        self._manifest_strict = storage.staticfiles_storage.manifest_strict