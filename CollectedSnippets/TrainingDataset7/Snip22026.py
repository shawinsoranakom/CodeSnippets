def test_file_iteration_mixed_newlines(self):
        f = File(BytesIO(b"one\rtwo\nthree\r\nfour"))
        self.assertEqual(list(f), [b"one\r", b"two\n", b"three\r\n", b"four"])