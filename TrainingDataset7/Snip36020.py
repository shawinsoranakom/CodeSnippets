def setUp(self):
        _directory = tempfile.TemporaryDirectory()
        self.addCleanup(_directory.cleanup)
        self.directory = Path(_directory.name).resolve(strict=True).absolute()
        self.file = self.directory / "test"
        self.file.touch()