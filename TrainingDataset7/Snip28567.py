def test_initial_form_count_empty_data(self):
        AuthorFormSet = modelformset_factory(Author, fields="__all__")
        formset = AuthorFormSet({})
        self.assertEqual(formset.initial_form_count(), 0)