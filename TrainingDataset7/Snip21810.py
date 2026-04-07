def test_valid_names(self):
        storage = self.storage_class()
        name = "UnTRIVíAL @fil$ena#me!"
        valid_name = storage.get_valid_name(name)
        candidates = [
            (name, valid_name),
            (f"././././././{name}", valid_name),
            (f"some/path/{name}", f"some/path/{valid_name}"),
            (f"some/./path/./{name}", f"some/path/{valid_name}"),
            (f"././some/././path/./{name}", f"some/path/{valid_name}"),
            (f".\\.\\.\\.\\.\\.\\{name}", valid_name),
            (f"some\\path\\{name}", f"some/path/{valid_name}"),
            (f"some\\.\\path\\.\\{name}", f"some/path/{valid_name}"),
            (f".\\.\\some\\.\\.\\path\\.\\{name}", f"some/path/{valid_name}"),
        ]
        for name, expected in candidates:
            with self.subTest(name=name):
                result = storage.generate_filename(name)
                self.assertEqual(result, os.path.normpath(expected))