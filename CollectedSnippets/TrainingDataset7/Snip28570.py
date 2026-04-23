def test_edit_only_object_outside_of_queryset(self):
        charles = Author.objects.create(name="Charles Baudelaire")
        walt = Author.objects.create(name="Walt Whitman")
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-0-id": walt.pk,
            "form-0-name": "Parth Patil",
        }
        AuthorFormSet = modelformset_factory(Author, fields="__all__", edit_only=True)
        formset = AuthorFormSet(data, queryset=Author.objects.filter(pk=charles.pk))
        self.assertIs(formset.is_valid(), True)
        formset.save()
        self.assertCountEqual(Author.objects.all(), [charles, walt])