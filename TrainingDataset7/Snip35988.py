def test_extract_function_traversal(self):
        archives_dir = os.path.join(os.path.dirname(__file__), "traversal_archives")
        tests = [
            ("traversal.tar", ".."),
            ("traversal_absolute.tar", "/tmp/evil.py"),
        ]
        if sys.platform == "win32":
            tests += [
                ("traversal_disk_win.tar", "d:evil.py"),
                ("traversal_disk_win.zip", "d:evil.py"),
            ]
        msg = "Archive contains invalid path: '%s'"
        for entry, invalid_path in tests:
            with self.subTest(entry), tempfile.TemporaryDirectory() as tmpdir:
                with self.assertRaisesMessage(SuspiciousOperation, msg % invalid_path):
                    archive.extract(os.path.join(archives_dir, entry), tmpdir)