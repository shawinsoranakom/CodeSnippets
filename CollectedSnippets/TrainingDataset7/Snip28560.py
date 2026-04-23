def test_get_queryset_unchanged_when_already_totally_ordered(self):
        # Ordering by pk is already totally ordered; pk must not be
        # appended again.
        AuthorFormSet = modelformset_factory(Author, fields="__all__")
        formset = AuthorFormSet(queryset=Author.objects.order_by("pk"))

        queryset = formset.get_queryset()
        # Must be exactly ("pk",), not ("pk", "pk").
        self.assertEqual(queryset.query.order_by, ("pk",))
        self.assertIs(queryset.totally_ordered, True)