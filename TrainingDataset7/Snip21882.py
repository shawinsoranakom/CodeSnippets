def test_file_methods_pathlib_path(self):
        p = Path("test.file")
        self.assertFalse(self.storage.exists(p))
        f = ContentFile("custom contents")
        f_name = self.storage.save(p, f)
        # Storage basic methods.
        self.assertEqual(self.storage.path(p), os.path.join(self.temp_dir, p))
        self.assertEqual(self.storage.size(p), 15)
        self.assertEqual(self.storage.url(p), self.storage.base_url + f_name)
        with self.storage.open(p) as f:
            self.assertEqual(f.read(), b"custom contents")
        self.addCleanup(self.storage.delete, p)