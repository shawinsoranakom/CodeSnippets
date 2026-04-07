def setUp(self):
        super().setUp()
        self.tmp_dir = self.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir)
        _settings_override = override_settings(EMAIL_FILE_PATH=self.tmp_dir)
        _settings_override.enable()
        self.addCleanup(_settings_override.disable)