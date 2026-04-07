def test_size_changing_after_writing(self):
        """ContentFile.size changes after a write()."""
        f = ContentFile("")
        self.assertEqual(f.size, 0)
        f.write("Test ")
        f.write("string")
        self.assertEqual(f.size, 11)
        with f.open() as fh:
            self.assertEqual(fh.read(), "Test string")