def test_beginning_with_slash(self):
        msg = (
            "Your URL pattern '%s' has a route beginning with a '/'. Remove "
            "this slash as it is unnecessary. If this pattern is targeted in "
            "an include(), ensure the include() pattern has a trailing '/'."
        )
        warning1, warning2 = check_url_config(None)
        self.assertEqual(warning1.id, "urls.W002")
        self.assertEqual(warning1.msg, msg % "/path-starting-with-slash/")
        self.assertEqual(warning2.id, "urls.W002")
        self.assertEqual(warning2.msg, msg % "/url-starting-with-slash/$")