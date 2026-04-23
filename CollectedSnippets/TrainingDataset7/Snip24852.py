def test_samesite(self):
        c = SimpleCookie("name=value; samesite=lax; httponly")
        self.assertEqual(c["name"]["samesite"], "lax")
        self.assertIn("SameSite=lax", c.output())