def test_not_modified_since(self):
        file_name = "file.txt"
        response = self.client.get(
            "/%s/%s" % (self.prefix, file_name),
            headers={
                # This is 24h before max Unix time. Remember to fix Django and
                # update this test well before 2038 :)
                "if-modified-since": "Mon, 18 Jan 2038 05:14:07 GMT"
            },
        )
        self.assertIsInstance(response, HttpResponseNotModified)