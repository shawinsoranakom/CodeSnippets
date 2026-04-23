def test_create_view_without_explicit_fields(self):
        class MyCreateView(CreateView):
            model = Author

        message = (
            "Using ModelFormMixin (base class of MyCreateView) without the "
            "'fields' attribute is prohibited."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            MyCreateView().get_form_class()