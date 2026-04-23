def test_path_with_embedded_null_bytes(self):
        for path in (
            "embedded_null_byte\x00.py",
            "di\x00rectory/embedded_null_byte.py",
        ):
            with self.subTest(path=path):
                self.assertEqual(
                    autoreload.iter_modules_and_files((), frozenset([path])),
                    frozenset(),
                )