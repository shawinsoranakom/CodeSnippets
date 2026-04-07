def test_urlencode(self):
        self.assertEqual(urlencode("fran\xe7ois & jill"), "fran%C3%A7ois%20%26%20jill")