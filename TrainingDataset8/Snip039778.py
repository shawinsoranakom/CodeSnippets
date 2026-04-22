def setUp(self) -> None:
        self._home = tempfile.mkdtemp()
        self._old_home = os.environ["HOME"]
        os.environ["HOME"] = self._home

        self._fd, self._path = tempfile.mkstemp()

        super().setUp()