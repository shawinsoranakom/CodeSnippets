def test_custom_upload_handler(self):
        file = tempfile.NamedTemporaryFile
        with file() as smallfile, file() as bigfile:
            # A small file (under the 5M quota)
            smallfile.write(b"a" * (2**21))
            smallfile.seek(0)

            # A big file (over the quota)
            bigfile.write(b"a" * (10 * 2**20))
            bigfile.seek(0)

            # Small file posting should work.
            self.assertIn("f", self.client.post("/quota/", {"f": smallfile}).json())

            # Large files don't go through.
            self.assertNotIn("f", self.client.post("/quota/", {"f": bigfile}).json())