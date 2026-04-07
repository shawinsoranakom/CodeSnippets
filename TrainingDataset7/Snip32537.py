def test_read_manifest(self):
        self.assertEqual(
            self.staticfiles_storage.read_manifest(),
            json.dumps(self.manifest),
        )