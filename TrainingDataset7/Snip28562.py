def test_prevent_change_outer_model_and_create_invalid_data(self):
        author = Author.objects.create(name="Charles")
        other_author = Author.objects.create(name="Walt")
        AuthorFormSet = modelformset_factory(Author, fields="__all__")
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "2",
            "form-MAX_NUM_FORMS": "",
            "form-0-id": str(author.id),
            "form-0-name": "Charles",
            "form-1-id": str(other_author.id),  # A model not in the formset's queryset.
            "form-1-name": "Changed name",
        }
        # This formset is only for Walt Whitman and shouldn't accept data for
        # other_author.
        formset = AuthorFormSet(
            data=data, queryset=Author.objects.filter(id__in=(author.id,))
        )
        self.assertTrue(formset.is_valid())
        formset.save()
        # The name of other_author shouldn't be changed and new models aren't
        # created.
        self.assertSequenceEqual(Author.objects.all(), [author, other_author])