def test_max_age_int(self):
        response = HttpResponse()
        response.set_cookie("max_age", max_age=10.6)
        self.assertEqual(response.cookies["max_age"]["max-age"], 10)