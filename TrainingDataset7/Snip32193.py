def test_can_use_salt(self):
        response = HttpResponse()
        response.set_signed_cookie("a", "hello", salt="one")
        request = HttpRequest()
        request.COOKIES["a"] = response.cookies["a"].value
        value = request.get_signed_cookie("a", salt="one")
        self.assertEqual(value, "hello")
        with self.assertRaises(signing.BadSignature):
            request.get_signed_cookie("a", salt="two")