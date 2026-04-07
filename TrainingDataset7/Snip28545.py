def test_modelformset_validate_max_flag(self):
        # If validate_max is set and max_num is less than TOTAL_FORMS in the
        # data, then throw an exception. MAX_NUM_FORMS in the data is
        # irrelevant here (it's output as a hint for the client but its
        # value in the returned data is not checked)

        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "2",  # should be ignored
            "form-0-price": "12.00",
            "form-0-quantity": "1",
            "form-1-price": "24.00",
            "form-1-quantity": "2",
        }

        FormSet = modelformset_factory(
            Price, fields="__all__", extra=1, max_num=1, validate_max=True
        )
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset.non_form_errors(), ["Please submit at most 1 form."])

        # Now test the same thing without the validate_max flag to ensure
        # default behavior is unchanged
        FormSet = modelformset_factory(Price, fields="__all__", extra=1, max_num=1)
        formset = FormSet(data)
        self.assertTrue(formset.is_valid())