def test_class_based_view_with_args(self):
        self.assertEqual("/params-cbv/5/", resolve_url(params_cbv, 5))