def test_url_params_from_lookup_dict_any_iterable(self):
        lookup1 = widgets.url_params_from_lookup_dict({"color__in": ("red", "blue")})
        lookup2 = widgets.url_params_from_lookup_dict({"color__in": ["red", "blue"]})
        self.assertEqual(lookup1, {"color__in": "red,blue"})
        self.assertEqual(lookup1, lookup2)