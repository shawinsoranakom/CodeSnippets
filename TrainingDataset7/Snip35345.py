def test_form_index_too_big(self):
        msg = (
            "The formset <TestFormset: bound=True valid=False total_forms=1> only has "
            "1 form."
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertFormSetError(TestFormset.invalid(), 2, "field", "error")