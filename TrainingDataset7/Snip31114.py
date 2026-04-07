def test_custom_multipart_parser_class(self):

        class CustomMultiPartParser(MultiPartParser):
            def parse(self):
                post, files = super().parse()
                post._mutable = True
                post["custom_parser_used"] = "yes"
                post._mutable = False
                return post, files

        class CustomWSGIRequest(WSGIRequest):
            multipart_parser_class = CustomMultiPartParser

        payload = FakePayload(
            "\r\n".join(
                [
                    "--boundary",
                    'Content-Disposition: form-data; name="name"',
                    "",
                    "value",
                    "--boundary--",
                ]
            )
        )
        request = CustomWSGIRequest(
            {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": "multipart/form-data; boundary=boundary",
                "CONTENT_LENGTH": len(payload),
                "wsgi.input": payload,
            }
        )
        self.assertEqual(request.POST.get("custom_parser_used"), "yes")
        self.assertEqual(request.POST.get("name"), "value")