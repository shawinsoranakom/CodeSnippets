def test_samesite(self):
        response = HttpResponse()
        response.set_cookie("example", samesite="None")
        self.assertEqual(response.cookies["example"]["samesite"], "None")
        response.set_cookie("example", samesite="Lax")
        self.assertEqual(response.cookies["example"]["samesite"], "Lax")
        response.set_cookie("example", samesite="strict")
        self.assertEqual(response.cookies["example"]["samesite"], "strict")