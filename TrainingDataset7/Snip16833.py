def test_url_params_from_lookup_dict_callable(self):
        def my_callable():
            return "works"

        lookup1 = widgets.url_params_from_lookup_dict({"myfield": my_callable})
        lookup2 = widgets.url_params_from_lookup_dict({"myfield": my_callable()})
        self.assertEqual(lookup1, lookup2)