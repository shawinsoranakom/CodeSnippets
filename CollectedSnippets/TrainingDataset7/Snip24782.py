def test_urlencode_int(self):
        # Normally QueryDict doesn't contain non-string values but lazily
        # written tests may make that mistake.
        q = QueryDict(mutable=True)
        q["a"] = 1
        self.assertEqual(q.urlencode(), "a=1")