def test_submit_button_outside_form(self):
        """Test that a submit button is not allowed outside a form."""

        with self.assertRaises(StreamlitAPIException) as ctx:
            st.form_submit_button()

        self.assertIn(
            "`st.form_submit_button()` must be used inside an `st.form()`",
            str(ctx.exception),
        )