def test_max_age_expiration(self):
        """Cookie will expire if max_age is provided."""
        response = HttpResponse()
        set_cookie_time = time.time()
        with freeze_time(set_cookie_time):
            response.set_cookie("max_age", max_age=10)
        max_age_cookie = response.cookies["max_age"]
        self.assertEqual(max_age_cookie["max-age"], 10)
        self.assertEqual(max_age_cookie["expires"], http_date(set_cookie_time + 10))