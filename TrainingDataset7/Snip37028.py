def test_i18n_english_variant(self):
        with override("en-gb"):
            response = self.client.get("/jsi18n/")
            self.assertIn(
                '"this color is to be translated": "this colour is to be translated"',
                response.context["catalog_str"],
            )