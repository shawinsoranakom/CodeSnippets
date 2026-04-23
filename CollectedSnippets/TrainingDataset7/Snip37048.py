def test_is_modified_since(self):
        file_name = "file.txt"
        response = self.client.get(
            "/%s/%s" % (self.prefix, file_name),
            headers={"if-modified-since": "Thu, 1 Jan 1970 00:00:00 GMT"},
        )
        response_content = b"".join(response)
        with open(path.join(media_dir, file_name), "rb") as fp:
            self.assertEqual(fp.read(), response_content)