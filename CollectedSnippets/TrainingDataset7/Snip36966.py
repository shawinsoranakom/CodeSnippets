def test_cleanse_session_cookie_value(self):
        self.client.cookies.load({"djangosession": "should not be displayed"})
        response = self.client.get("/raises500/")
        self.assertNotContains(response, "should not be displayed", status_code=500)