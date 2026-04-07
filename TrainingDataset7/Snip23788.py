def test_get_form(self):
        class TestFormMixin(FormMixin):
            request = self.request_factory.get("/")

        self.assertIsInstance(
            TestFormMixin().get_form(forms.Form),
            forms.Form,
            "get_form() should use provided form class.",
        )

        class FormClassTestFormMixin(TestFormMixin):
            form_class = forms.Form

        self.assertIsInstance(
            FormClassTestFormMixin().get_form(),
            forms.Form,
            "get_form() should fallback to get_form_class() if none is provided.",
        )