def test_i18n_language_english_default(self):
        """
        Check if the JavaScript i18n view returns a complete language catalog
        if the default language is en-us, the selected language has a
        translation available and a catalog composed by djangojs domain
        translations of multiple Python packages is requested. See #13388,
        #3594 and #13514 for more details.
        """
        base_trans_string = (
            "il faut traduire cette cha\\u00eene de caract\\u00e8res de "
        )
        app1_trans_string = base_trans_string + "app1"
        app2_trans_string = base_trans_string + "app2"
        with self.settings(LANGUAGE_CODE="en-us"), override("fr"):
            response = self.client.get("/jsi18n_multi_packages1/")
            self.assertContains(response, app1_trans_string)
            self.assertContains(response, app2_trans_string)

            response = self.client.get("/jsi18n/app1/")
            self.assertContains(response, app1_trans_string)
            self.assertNotContains(response, app2_trans_string)

            response = self.client.get("/jsi18n/app2/")
            self.assertNotContains(response, app1_trans_string)
            self.assertContains(response, app2_trans_string)