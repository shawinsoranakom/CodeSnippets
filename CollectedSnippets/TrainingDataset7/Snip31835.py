def test_no_collectstatic_emulation(self):
        """
        LiveServerTestCase reports a 404 status code when HTTP client
        tries to access a static file that isn't explicitly put under
        STATIC_ROOT.
        """
        with self.assertRaises(HTTPError) as err:
            self.urlopen("/static/another_app/another_app_static_file.txt")
        err.exception.close()
        self.assertEqual(err.exception.code, 404, "Expected 404 response")