def test_form_index_too_big_plural(self):
        formset = TestFormset(
            {
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "0",
                "form-0-field": "valid",
                "form-1-field": "valid",
            }
        )
        formset.full_clean()
        msg = (
            "The formset <TestFormset: bound=True valid=True total_forms=2> only has 2 "
            "forms."
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertFormSetError(formset, 2, "field", "error")