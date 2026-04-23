def test_big_base64_newlines_upload(self):
        self._test_base64_upload("Big data" * 68000, encode=base64.encodebytes)