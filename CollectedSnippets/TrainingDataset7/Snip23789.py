def test_get_context_data(self):
        class FormContext(FormMixin):
            request = self.request_factory.get("/")
            form_class = forms.Form

        self.assertIsInstance(FormContext().get_context_data()["form"], forms.Form)