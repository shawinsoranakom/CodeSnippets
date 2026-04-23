def test_httponly_cookie(self):
        response = HttpResponse()
        response.set_cookie("example", httponly=True)
        example_cookie = response.cookies["example"]
        self.assertIn(
            "; %s" % cookies.Morsel._reserved["httponly"], str(example_cookie)
        )
        self.assertIs(example_cookie["httponly"], True)