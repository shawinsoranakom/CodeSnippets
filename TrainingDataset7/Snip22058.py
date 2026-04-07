def test_file_move_ensure_truncation(self):
        with tempfile.NamedTemporaryFile(delete=False) as src:
            src.write(b"content")
            src_name = src.name
        self.addCleanup(
            lambda: os.remove(src_name) if os.path.exists(src_name) else None
        )

        with tempfile.NamedTemporaryFile(delete=False) as dest:
            dest.write(b"This is a longer content.")
            dest_name = dest.name
        self.addCleanup(os.remove, dest_name)

        with mock.patch("django.core.files.move.os.rename", side_effect=OSError()):
            file_move_safe(src_name, dest_name, allow_overwrite=True)

        with open(dest_name, "rb") as f:
            content = f.read()

        self.assertEqual(content, b"content")