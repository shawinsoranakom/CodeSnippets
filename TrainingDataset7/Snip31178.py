def test_delete_cookie_samesite(self):
        response = HttpResponse()
        response.delete_cookie("c", samesite="lax")
        self.assertEqual(response.cookies["c"]["samesite"], "lax")