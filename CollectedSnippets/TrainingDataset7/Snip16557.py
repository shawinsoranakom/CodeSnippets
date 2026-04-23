def test_JS_i18n(self):
        "Check the never-cache status of the JavaScript i18n view"
        response = self.client.get(reverse("admin:jsi18n"))
        self.assertIsNone(get_max_age(response))