def test_max_age_with_expires(self):
        response = HttpResponse()
        msg = "'expires' and 'max_age' can't be used together."
        with self.assertRaisesMessage(ValueError, msg):
            response.set_cookie(
                "max_age", expires=datetime(2000, 1, 1), max_age=timedelta(hours=1)
            )