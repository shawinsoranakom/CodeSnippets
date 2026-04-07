def test_delete_deletes_directories(self):
        tmp_dir = tempfile.mkdtemp(dir=self.storage.location)
        self.storage.delete(tmp_dir)
        self.assertFalse(os.path.exists(tmp_dir))