def test_unicode_file_name(self):
        with sys_tempfile.TemporaryDirectory() as temp_dir:
            # This file contains Chinese symbols and an accented char in the
            # name.
            with open(os.path.join(temp_dir, UNICODE_FILENAME), "w+b") as file1:
                file1.write(b"b" * (2**10))
                file1.seek(0)
                response = self.client.post("/unicode_name/", {"file_unicode": file1})
            self.assertEqual(response.status_code, 200)