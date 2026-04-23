def test_get_form(self):
        form_class = views.AuthorGetQuerySetFormView().get_form_class()
        self.assertEqual(form_class._meta.model, Author)