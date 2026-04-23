def test_custom_queryset_init(self):
        """
        A queryset can be overridden in the formset's __init__() method.
        """
        Author.objects.create(name="Charles Baudelaire")
        Author.objects.create(name="Paul Verlaine")

        class BaseAuthorFormSet(BaseModelFormSet):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.queryset = Author.objects.filter(name__startswith="Charles")

        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", formset=BaseAuthorFormSet
        )
        formset = AuthorFormSet()
        self.assertEqual(len(formset.get_queryset()), 1)