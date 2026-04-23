def test_invalid_samesite(self):
        msg = 'samesite must be "lax", "none", or "strict".'
        with self.assertRaisesMessage(ValueError, msg):
            HttpResponse().set_cookie("example", samesite="invalid")