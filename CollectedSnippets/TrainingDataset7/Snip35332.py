def test_multiple_forms(self):
        formset = TestFormset(
            {
                "form-TOTAL_FORMS": "2",
                "form-INITIAL_FORMS": "0",
                "form-0-field": "valid",
                "form-1-field": "invalid",
            }
        )
        formset.full_clean()
        self.assertFormSetError(formset, 0, "field", [])
        self.assertFormSetError(formset, 1, "field", ["invalid value"])