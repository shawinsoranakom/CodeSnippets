def test_get_prefix(self):
        """Test prefix can be set (see #18872)"""
        test_string = "test"

        get_request = self.request_factory.get("/")

        class TestFormMixin(FormMixin):
            request = get_request

        default_kwargs = TestFormMixin().get_form_kwargs()
        self.assertIsNone(default_kwargs.get("prefix"))

        set_mixin = TestFormMixin()
        set_mixin.prefix = test_string
        set_kwargs = set_mixin.get_form_kwargs()
        self.assertEqual(test_string, set_kwargs.get("prefix"))