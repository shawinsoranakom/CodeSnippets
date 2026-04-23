def setUp(self):
        _tempdir = tempfile.TemporaryDirectory()
        self.tempdir = Path(_tempdir.name).resolve(strict=True).absolute()
        self.existing_file = self.ensure_file(self.tempdir / "test.py")
        self.nonexistent_file = (self.tempdir / "does_not_exist.py").absolute()
        self.reloader = self.RELOADER_CLS()
        self.addCleanup(self.reloader.stop)
        self.addCleanup(_tempdir.cleanup)