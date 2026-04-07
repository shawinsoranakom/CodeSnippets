def test_get_language_from_request_code_too_long(self):
        request = self.rf.get("/", headers={"accept-language": "a" * 501})
        lang = get_language_from_request(request)
        self.assertEqual("en-us", lang)