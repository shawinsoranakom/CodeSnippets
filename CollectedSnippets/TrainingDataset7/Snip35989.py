def test_extract_function_traversal_startswith(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = os.path.abspath(tmpdir)
            tarfile_handle = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            tar_path = tarfile_handle.name
            tarfile_handle.close()
            self.addCleanup(os.remove, tar_path)

            malicious_member = os.path.join(base + "abc", "evil.txt")
            with zipfile.ZipFile(tar_path, "w") as zf:
                zf.writestr(malicious_member, "evil\n")
                zf.writestr("test.txt", "data\n")

            with self.assertRaisesMessage(
                SuspiciousOperation, "Archive contains invalid path"
            ):
                archive.extract(tar_path, base)