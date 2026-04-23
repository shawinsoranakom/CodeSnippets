def test_urlencoded(self):
        self.assertEqual(
            iriencode(urlencode("fran\xe7ois & jill")), "fran%C3%A7ois%20%26%20jill"
        )