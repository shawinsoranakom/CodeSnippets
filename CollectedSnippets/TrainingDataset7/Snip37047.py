def test_copes_with_empty_path_component(self):
        file_name = "file.txt"
        response = self.client.get("/%s//%s" % (self.prefix, file_name))
        response_content = b"".join(response)
        with open(path.join(media_dir, file_name), "rb") as fp:
            self.assertEqual(fp.read(), response_content)