def test_compress_file_response(self):
        """
        Compression is performed on FileResponse.
        """
        with open(__file__, "rb") as file1:

            def get_response(req):
                file_resp = FileResponse(file1)
                file_resp["Content-Type"] = "text/html; charset=UTF-8"
                return file_resp

            r = GZipMiddleware(get_response)(self.req)
            with open(__file__, "rb") as file2:
                self.assertEqual(self.decompress(b"".join(r)), file2.read())
            self.assertEqual(r.get("Content-Encoding"), "gzip")
            self.assertIsNot(r.file_to_stream, file1)