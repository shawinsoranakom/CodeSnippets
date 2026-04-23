def test_max_num(self):
        # Test the behavior of max_num with model formsets. It should allow
        # all existing related objects/inlines for a given object to be
        # displayed, but not allow the creation of new inlines beyond max_num.

        a1 = Author.objects.create(name="Charles Baudelaire")
        a2 = Author.objects.create(name="Paul Verlaine")
        a3 = Author.objects.create(name="Walt Whitman")

        qs = Author.objects.order_by("name")

        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", max_num=None, extra=3
        )
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 6)
        self.assertEqual(len(formset.extra_forms), 3)

        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", max_num=4, extra=3
        )
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 4)
        self.assertEqual(len(formset.extra_forms), 1)

        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", max_num=0, extra=3
        )
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 3)
        self.assertEqual(len(formset.extra_forms), 0)

        AuthorFormSet = modelformset_factory(Author, fields="__all__", max_num=None)
        formset = AuthorFormSet(queryset=qs)
        self.assertSequenceEqual(formset.get_queryset(), [a1, a2, a3])

        AuthorFormSet = modelformset_factory(Author, fields="__all__", max_num=0)
        formset = AuthorFormSet(queryset=qs)
        self.assertSequenceEqual(formset.get_queryset(), [a1, a2, a3])

        AuthorFormSet = modelformset_factory(Author, fields="__all__", max_num=4)
        formset = AuthorFormSet(queryset=qs)
        self.assertSequenceEqual(formset.get_queryset(), [a1, a2, a3])