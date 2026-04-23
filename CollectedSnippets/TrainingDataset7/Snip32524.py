def test_manifest_hash(self):
        # Collect the additional file.
        self.run_collectstatic()

        _, manifest_hash_orig = storage.staticfiles_storage.load_manifest()
        self.assertNotEqual(manifest_hash_orig, "")
        self.assertEqual(storage.staticfiles_storage.manifest_hash, manifest_hash_orig)
        # Saving doesn't change the hash.
        storage.staticfiles_storage.save_manifest()
        self.assertEqual(storage.staticfiles_storage.manifest_hash, manifest_hash_orig)
        # Delete the original file from the app, collect with clear.
        os.unlink(self._clear_filename)
        self.run_collectstatic(clear=True)
        # Hash is changed.
        _, manifest_hash = storage.staticfiles_storage.load_manifest()
        self.assertNotEqual(manifest_hash, manifest_hash_orig)