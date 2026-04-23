def test_get_form_checks_for_object(self):
        mixin = ModelFormMixin()
        mixin.request = RequestFactory().get("/")
        self.assertEqual({"initial": {}, "prefix": None}, mixin.get_form_kwargs())