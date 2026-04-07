def test_reason_phrase_setter(self):
        r = HttpResponseBase()
        r.reason_phrase = "test"
        self.assertEqual(r.reason_phrase, "test")