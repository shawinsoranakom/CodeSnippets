def test_broken_custom_upload_handler(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(b"a" * (2**21))
            file.seek(0)

            msg = (
                "You cannot alter upload handlers after the upload has been processed."
            )
            with self.assertRaisesMessage(AttributeError, msg):
                self.client.post("/quota/broken/", {"f": file})