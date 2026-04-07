def test_file_content(self):
        file = tempfile.NamedTemporaryFile
        with (
            file(suffix=".ctype_extra") as no_content_type,
            file(suffix=".ctype_extra") as simple_file,
        ):
            no_content_type.write(b"no content")
            no_content_type.seek(0)

            simple_file.write(b"text content")
            simple_file.seek(0)
            simple_file.content_type = "text/plain"

            string_io = StringIO("string content")
            bytes_io = BytesIO(b"binary content")

            response = self.client.post(
                "/echo_content/",
                {
                    "no_content_type": no_content_type,
                    "simple_file": simple_file,
                    "string": string_io,
                    "binary": bytes_io,
                },
            )
            received = response.json()
            self.assertEqual(received["no_content_type"], "no content")
            self.assertEqual(received["simple_file"], "text content")
            self.assertEqual(received["string"], "string content")
            self.assertEqual(received["binary"], "binary content")