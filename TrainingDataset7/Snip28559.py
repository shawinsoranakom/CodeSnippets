def test_get_queryset_appends_pk_to_meta_ordering(self):
        # Author has Meta.ordering = ("name",) which is not deterministic
        # by itself.
        AuthorFormSet = modelformset_factory(Author, fields="__all__")
        formset = AuthorFormSet()

        queryset = formset.get_queryset()
        self.assertEqual(queryset.query.order_by, ("name", "pk"))