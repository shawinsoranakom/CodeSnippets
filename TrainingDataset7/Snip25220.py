def test_unsaved_fk_validate_unique(self):
        poet = Poet(name="unsaved")
        PoemFormSet = inlineformset_factory(Poet, Poem, fields=["name"])
        data = {
            "poem_set-TOTAL_FORMS": "2",
            "poem_set-INITIAL_FORMS": "0",
            "poem_set-MAX_NUM_FORMS": "2",
            "poem_set-0-name": "Poem",
            "poem_set-1-name": "Poem",
        }
        formset = PoemFormSet(data, instance=poet)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset.non_form_errors(), ["Please correct the duplicate data for name."]
        )