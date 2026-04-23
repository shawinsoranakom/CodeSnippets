def test_inlineformset_factory_absolute_max(self):
        author = Author.objects.create(name="Charles Baudelaire")
        BookFormSet = inlineformset_factory(
            Author,
            Book,
            fields="__all__",
            absolute_max=1500,
        )
        data = {
            "book_set-TOTAL_FORMS": "1501",
            "book_set-INITIAL_FORMS": "0",
            "book_set-MAX_NUM_FORMS": "0",
        }
        formset = BookFormSet(data, instance=author)
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(len(formset.forms), 1500)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 1000 forms."],
        )