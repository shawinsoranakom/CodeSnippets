def test_large_upload(self):
        file = tempfile.NamedTemporaryFile
        with file(suffix=".file1") as file1, file(suffix=".file2") as file2:
            file1.write(b"a" * (2**21))
            file1.seek(0)

            file2.write(b"a" * (10 * 2**20))
            file2.seek(0)

            post_data = {
                "name": "Ringo",
                "file_field1": file1,
                "file_field2": file2,
            }

            for key in list(post_data):
                try:
                    post_data[key + "_hash"] = hashlib.sha1(
                        post_data[key].read()
                    ).hexdigest()
                    post_data[key].seek(0)
                except AttributeError:
                    post_data[key + "_hash"] = hashlib.sha1(
                        post_data[key].encode()
                    ).hexdigest()

            response = self.client.post("/verify/", post_data)

            self.assertEqual(response.status_code, 200)