def test_extract_function(self):
        with os.scandir(self.testdir) as entries:
            for entry in entries:
                with self.subTest(entry.name), tempfile.TemporaryDirectory() as tmpdir:
                    if (entry.name.endswith(".bz2") and not HAS_BZ2) or (
                        entry.name.endswith((".lzma", ".xz")) and not HAS_LZMA
                    ):
                        continue
                    archive.extract(entry.path, tmpdir)
                    self.assertTrue(os.path.isfile(os.path.join(tmpdir, "1")))
                    self.assertTrue(os.path.isfile(os.path.join(tmpdir, "2")))
                    self.assertTrue(os.path.isfile(os.path.join(tmpdir, "foo", "1")))
                    self.assertTrue(os.path.isfile(os.path.join(tmpdir, "foo", "2")))
                    self.assertTrue(
                        os.path.isfile(os.path.join(tmpdir, "foo", "bar", "1"))
                    )
                    self.assertTrue(
                        os.path.isfile(os.path.join(tmpdir, "foo", "bar", "2"))
                    )