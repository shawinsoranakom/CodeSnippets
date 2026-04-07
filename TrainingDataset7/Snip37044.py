def test_serve(self):
        "The static view can serve static media"
        media_files = ["file.txt", "file.txt.gz", "%2F.txt"]
        for filename in media_files:
            response = self.client.get("/%s/%s" % (self.prefix, quote(filename)))
            response_content = b"".join(response)
            file_path = path.join(media_dir, filename)
            with open(file_path, "rb") as fp:
                self.assertEqual(fp.read(), response_content)
            self.assertEqual(
                len(response_content), int(response.headers["Content-Length"])
            )
            self.assertEqual(
                mimetypes.guess_type(file_path)[1],
                response.get("Content-Encoding", None),
            )