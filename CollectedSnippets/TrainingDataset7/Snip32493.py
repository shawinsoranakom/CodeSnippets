def test_import_replacement(self):
        "See #18050"
        relpath = self.hashed_file_path("cached/import.css")
        self.assertEqual(relpath, "cached/import.f53576679e5a.css")
        with storage.staticfiles_storage.open(relpath) as relfile:
            self.assertIn(b"""import url("styles.5e0040571e1a.css")""", relfile.read())
        self.assertPostCondition()