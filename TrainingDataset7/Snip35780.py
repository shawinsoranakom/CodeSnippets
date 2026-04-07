def test_view_func_from_cbv_no_expected_kwarg(self):
        with self.assertRaises(NoReverseMatch):
            reverse(views.view_func_from_cbv)