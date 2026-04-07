def test_open_resets_file_to_start_and_returns_context_manager(self):
        uf = InMemoryUploadedFile(StringIO("1"), "", "test", "text/plain", 1, "utf8")
        uf.read()
        with uf.open() as f:
            self.assertEqual(f.read(), "1")