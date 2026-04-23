def test_model_formset_with_initial_queryset(self):
        # has_changed should work with queryset and list of pk's
        # see #18898
        FormSet = modelformset_factory(AuthorMeeting, fields="__all__")
        Author.objects.create(pk=1, name="Charles Baudelaire")
        data = {
            "form-TOTAL_FORMS": 1,
            "form-INITIAL_FORMS": 0,
            "form-MAX_NUM_FORMS": "",
            "form-0-name": "",
            "form-0-created": "",
            "form-0-authors": list(Author.objects.values_list("id", flat=True)),
        }
        formset = FormSet(initial=[{"authors": Author.objects.all()}], data=data)
        self.assertFalse(formset.extra_forms[0].has_changed())