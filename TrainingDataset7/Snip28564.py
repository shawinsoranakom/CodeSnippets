def test_validation_with_child_model_without_id(self):
        BetterAuthorFormSet = modelformset_factory(BetterAuthor, fields="__all__")
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "",
            "form-0-name": "Charles",
            "form-0-write_speed": "10",
        }
        formset = BetterAuthorFormSet(data)
        self.assertEqual(
            formset.errors,
            [{"author_ptr": ["This field is required."]}],
        )