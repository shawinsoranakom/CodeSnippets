def test_multiple_forms_same_labels_different_keys(self):
        """Multiple forms with different keys are allowed."""

        try:
            st.form(key="foo")
            st.form(key="bar")

        except Exception:
            self.fail("Forms with same labels and different keys failed to create.")