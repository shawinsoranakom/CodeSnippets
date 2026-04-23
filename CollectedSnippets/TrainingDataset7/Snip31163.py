def test_near_expiration(self):
        """Cookie will expire when a near expiration time is provided."""
        response = HttpResponse()
        # There's a timing weakness in this test; The expected result for
        # max-age requires that there be a very slight difference between the
        # evaluated expiration time and the time evaluated in set_cookie(). If
        # this difference doesn't exist, the cookie time will be 1 second
        # larger. The sleep guarantees that there will be a time difference.
        expires = datetime.now(tz=UTC).replace(tzinfo=None) + timedelta(seconds=10)
        time.sleep(0.001)
        response.set_cookie("datetime", expires=expires)
        datetime_cookie = response.cookies["datetime"]
        self.assertEqual(datetime_cookie["max-age"], 10)