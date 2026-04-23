def test_jsi18n(self):
        """The javascript_catalog can be deployed with language settings"""
        for lang_code in ["es", "fr", "ru"]:
            with override(lang_code):
                catalog = gettext.translation("djangojs", locale_dir, [lang_code])
                trans_txt = catalog.gettext("this is to be translated")
                response = self.client.get("/jsi18n/")
                self.assertEqual(
                    response.headers["Content-Type"], 'text/javascript; charset="utf-8"'
                )
                # response content must include a line like:
                # "this is to be translated": <value of trans_txt Python
                # variable> json.dumps() is used to be able to check Unicode
                # strings.
                self.assertContains(response, json.dumps(trans_txt), 1)
                if lang_code == "fr":
                    # Message with context (msgctxt)
                    self.assertContains(response, '"month name\\u0004May": "mai"', 1)