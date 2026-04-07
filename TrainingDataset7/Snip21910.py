def test_stringio(self):
        # Test passing StringIO instance as content argument to save
        output = StringIO()
        output.write("content")
        output.seek(0)

        # Save it and read written file
        temp_storage.save("tests/stringio", output)
        self.assertTrue(temp_storage.exists("tests/stringio"))
        with temp_storage.open("tests/stringio") as f:
            self.assertEqual(f.read(), b"content")