def test_manifest_hash_v1(self):
        storage.staticfiles_storage.manifest_name = "staticfiles_v1.json"
        manifest_content, manifest_hash = storage.staticfiles_storage.load_manifest()
        self.assertEqual(manifest_hash, "")
        self.assertEqual(manifest_content, {"dummy.txt": "dummy.txt"})