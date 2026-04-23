def test_get_context_data_super(self):
        test_view = views.CustomContextView()
        context = test_view.get_context_data(kwarg_test="kwarg_value")

        # the test_name key is inserted by the test classes parent
        self.assertIn("test_name", context)
        self.assertEqual(context["kwarg_test"], "kwarg_value")
        self.assertEqual(context["custom_key"], "custom_value")

        # test that kwarg overrides values assigned higher up
        context = test_view.get_context_data(test_name="test_value")
        self.assertEqual(context["test_name"], "test_value")