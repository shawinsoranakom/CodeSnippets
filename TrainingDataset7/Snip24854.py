def test_load_dict(self):
        c = SimpleCookie()
        c.load({"name": "val"})
        self.assertEqual(c["name"].value, "val")