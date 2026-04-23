def setUp(self) -> None:
        self._test_dir = tempfile.TemporaryDirectory()

        create_file = lambda prefix, suffix: tempfile.NamedTemporaryFile(
            dir=self._test_dir.name,
            prefix=prefix,
            suffix=suffix,
            delete=False,
        )

        create_file("01", ".py")
        create_file("02", ".py")
        create_file("03", ".py")
        create_file("04", ".rs")
        create_file(".05", ".py")