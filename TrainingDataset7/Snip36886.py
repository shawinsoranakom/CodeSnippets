def test_default_urlconf_script_name(self):
        response = self.client.request(**{"path": "/FORCED_PREFIX/"})
        self.assertContains(
            response, "<h1>The install worked successfully! Congratulations!</h1>"
        )