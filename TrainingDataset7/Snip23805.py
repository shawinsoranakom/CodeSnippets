def test_define_both_fields_and_form_class(self):
        class MyCreateView(CreateView):
            model = Author
            form_class = AuthorForm
            fields = ["name"]

        message = "Specifying both 'fields' and 'form_class' is not permitted."
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            MyCreateView().get_form_class()