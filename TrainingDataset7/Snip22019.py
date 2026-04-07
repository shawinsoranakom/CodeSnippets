def test_open_resets_opened_file_to_start_and_returns_context_manager(self):
        file = File(BytesIO(b"content"))
        file.read()
        with file.open() as f:
            self.assertEqual(f.read(), b"content")