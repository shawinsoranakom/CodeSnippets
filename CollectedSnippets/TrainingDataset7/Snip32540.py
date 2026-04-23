def test_save_manifest_create(self):
        os.remove(self.manifest_file)
        self.staticfiles_storage.save_manifest()
        self.assertIs(self.manifest_file.exists(), True)
        new_manifest = json.loads(self.staticfiles_storage.read_manifest())
        self.assertIn("paths", new_manifest)
        self.assertNotEqual(new_manifest, self.manifest)