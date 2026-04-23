def test_inlineformset_factory_absolute_max_with_max_num(self):
        author = Author.objects.create(name="Charles Baudelaire")
        BookFormSet = inlineformset_factory(
            Author,
            Book,
            fields="__all__",
            max_num=20,
            absolute_max=100,
        )
        data = {
            "book_set-TOTAL_FORMS": "101",
            "book_set-INITIAL_FORMS": "0",
            "book_set-MAX_NUM_FORMS": "0",
        }
        formset = BookFormSet(data, instance=author)
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(len(formset.forms), 100)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 20 forms."],
        )