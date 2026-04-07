def test_urlencode(self):
        q = QueryDict(mutable=True)
        q["next"] = "/a&b/"
        self.assertEqual(q.urlencode(), "next=%2Fa%26b%2F")
        self.assertEqual(q.urlencode(safe="/"), "next=/a%26b/")
        q = QueryDict(mutable=True)
        q["next"] = "/t\xebst&key/"
        self.assertEqual(q.urlencode(), "next=%2Ft%C3%ABst%26key%2F")
        self.assertEqual(q.urlencode(safe="/"), "next=/t%C3%ABst%26key/")