def test_invalid_if_modified_since2(self):
        """Handle even more bogus If-Modified-Since values gracefully

        Assume that a file is modified since an invalid timestamp as per RFC
        9110 Section 13.1.3.
        """
        file_name = "file.txt"
        invalid_date = ": 1291108438, Wed, 20 Oct 2010 14:05:00 GMT"
        response = self.client.get(
            "/%s/%s" % (self.prefix, file_name),
            headers={"if-modified-since": invalid_date},
        )
        response_content = b"".join(response)
        with open(path.join(media_dir, file_name), "rb") as fp:
            self.assertEqual(fp.read(), response_content)
        self.assertEqual(len(response_content), int(response.headers["Content-Length"]))