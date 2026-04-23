def test_min_num(self):
        # Test the behavior of min_num with model formsets. It should be
        # added to extra.
        qs = Author.objects.none()

        AuthorFormSet = modelformset_factory(Author, fields="__all__", extra=0)
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 0)

        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", min_num=1, extra=0
        )
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 1)

        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", min_num=1, extra=1
        )
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 2)