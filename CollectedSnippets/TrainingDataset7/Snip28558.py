def test_get_queryset_appends_pk_to_explicit_queryset_ordering(self):
        # Author.name is non-unique, so order_by("name") is not totally
        # ordered.
        AuthorFormSet = modelformset_factory(Author, fields="__all__")
        formset = AuthorFormSet(queryset=Author.objects.order_by("name"))

        queryset = formset.get_queryset()
        self.assertEqual(queryset.query.order_by, ("name", "pk"))