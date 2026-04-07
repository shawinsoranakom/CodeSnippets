def test_class_based_view(self):
        self.assertEqual("/some-cbv/", resolve_url(some_cbv))