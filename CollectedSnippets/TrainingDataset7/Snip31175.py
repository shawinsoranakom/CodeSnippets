def test_default(self):
        response = HttpResponse()
        response.delete_cookie("c")
        cookie = response.cookies["c"]
        self.assertEqual(cookie["expires"], "Thu, 01 Jan 1970 00:00:00 GMT")
        self.assertEqual(cookie["max-age"], 0)
        self.assertEqual(cookie["path"], "/")
        self.assertEqual(cookie["secure"], "")
        self.assertEqual(cookie["domain"], "")
        self.assertEqual(cookie["samesite"], "")