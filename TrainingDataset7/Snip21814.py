def test_filefield_dangerous_filename_dot_segments(self):
        f = FileField(upload_to="some/folder/")
        msg = "Detected path traversal attempt in 'some/folder/../path'"
        with self.assertRaisesMessage(SuspiciousFileOperation, msg):
            f.generate_filename(None, "../path")