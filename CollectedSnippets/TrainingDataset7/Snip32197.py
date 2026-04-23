def test_set_signed_cookie_max_age_argument(self):
        response = HttpResponse()
        response.set_signed_cookie("c", "value", max_age=100)
        self.assertEqual(response.cookies["c"]["max-age"], 100)
        response.set_signed_cookie("d", "value", max_age=timedelta(hours=2))
        self.assertEqual(response.cookies["d"]["max-age"], 7200)