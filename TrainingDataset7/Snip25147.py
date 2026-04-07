def test_specific_language_codes(self):
        # issue 11915
        request = self.rf.get(
            "/", headers={"accept-language": "pt,en-US;q=0.8,en;q=0.6,ru;q=0.4"}
        )
        lang = get_language_from_request(request)
        self.assertEqual("pt-br", lang)

        request = self.rf.get(
            "/", headers={"accept-language": "pt-pt,en-US;q=0.8,en;q=0.6,ru;q=0.4"}
        )
        lang = get_language_from_request(request)
        self.assertEqual("pt-br", lang)