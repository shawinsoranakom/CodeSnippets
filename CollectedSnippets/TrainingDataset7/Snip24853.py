def test_httponly_after_load(self):
        c = SimpleCookie()
        c.load("name=val")
        c["name"]["httponly"] = True
        self.assertTrue(c["name"]["httponly"])