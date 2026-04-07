def test_missing_params_raise_no_reverse_match(self):
        with self.assertRaises(NoReverseMatch):
            resolve_url(params_view)

        with self.assertRaises(NoReverseMatch):
            resolve_url(params_cbv)