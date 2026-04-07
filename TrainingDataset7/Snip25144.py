def test_get_language_from_request(self):
        # issue 19919
        request = self.rf.get(
            "/", headers={"accept-language": "en-US,en;q=0.8,bg;q=0.6,ru;q=0.4"}
        )
        lang = get_language_from_request(request)
        self.assertEqual("en-us", lang)

        request = self.rf.get(
            "/", headers={"accept-language": "bg-bg,en-US;q=0.8,en;q=0.6,ru;q=0.4"}
        )
        lang = get_language_from_request(request)
        self.assertEqual("bg", lang)