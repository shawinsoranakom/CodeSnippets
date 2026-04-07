def test_fileupload_getlist(self):
        file = tempfile.NamedTemporaryFile
        with file() as file1, file() as file2, file() as file2a:
            file1.write(b"a" * (2**23))
            file1.seek(0)

            file2.write(b"a" * (2 * 2**18))
            file2.seek(0)

            file2a.write(b"a" * (5 * 2**20))
            file2a.seek(0)

            response = self.client.post(
                "/getlist_count/",
                {
                    "file1": file1,
                    "field1": "test",
                    "field2": "test3",
                    "field3": "test5",
                    "field4": "test6",
                    "field5": "test7",
                    "file2": (file2, file2a),
                },
            )
            got = response.json()
            self.assertEqual(got.get("file1"), 1)
            self.assertEqual(got.get("file2"), 2)