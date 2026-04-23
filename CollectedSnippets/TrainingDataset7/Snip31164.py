def test_aware_expiration(self):
        """set_cookie() accepts an aware datetime as expiration time."""
        response = HttpResponse()
        expires = datetime.now(tz=UTC) + timedelta(seconds=10)
        time.sleep(0.001)
        response.set_cookie("datetime", expires=expires)
        datetime_cookie = response.cookies["datetime"]
        self.assertEqual(datetime_cookie["max-age"], 10)