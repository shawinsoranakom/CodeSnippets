def test_delete_cookie_secure_samesite_none(self):
        # delete_cookie() sets the secure flag if samesite='none'.
        response = HttpResponse()
        response.delete_cookie("c", samesite="none")
        self.assertIs(response.cookies["c"]["secure"], True)