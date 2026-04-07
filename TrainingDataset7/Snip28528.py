def test_min_num_with_existing(self):
        # Test the behavior of min_num with existing objects.
        Author.objects.create(name="Charles Baudelaire")
        qs = Author.objects.all()

        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", extra=0, min_num=1
        )
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 1)