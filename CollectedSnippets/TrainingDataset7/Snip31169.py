def test_max_age_timedelta(self):
        response = HttpResponse()
        response.set_cookie("max_age", max_age=timedelta(hours=1))
        self.assertEqual(response.cookies["max_age"]["max-age"], 3600)