def test_form_block_data(self):
        """Test that a form creates a block element with correct data."""

        form_data = st.form(key="bar")._form_data
        self.assertEqual("bar", form_data.form_id)