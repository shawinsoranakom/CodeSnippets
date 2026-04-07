def test_content_type_extra(self):
        """Uploaded files may have content type parameters available."""
        file = tempfile.NamedTemporaryFile
        with (
            file(suffix=".ctype_extra") as no_content_type,
            file(suffix=".ctype_extra") as simple_file,
        ):
            no_content_type.write(b"something")
            no_content_type.seek(0)

            simple_file.write(b"something")
            simple_file.seek(0)
            simple_file.content_type = "text/plain; test-key=test_value"

            response = self.client.post(
                "/echo_content_type_extra/",
                {
                    "no_content_type": no_content_type,
                    "simple_file": simple_file,
                },
            )
            received = response.json()
            self.assertEqual(received["no_content_type"], {})
            self.assertEqual(received["simple_file"], {"test-key": "test_value"})