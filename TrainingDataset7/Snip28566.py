def test_validation_with_nonexistent_id(self):
        AuthorFormSet = modelformset_factory(Author, fields="__all__")
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "",
            "form-0-id": "12345",
            "form-0-name": "Charles",
        }
        formset = AuthorFormSet(data)
        self.assertEqual(
            formset.errors,
            [
                {
                    "id": [
                        "Select a valid choice. That choice is not one of the "
                        "available choices."
                    ]
                }
            ],
        )