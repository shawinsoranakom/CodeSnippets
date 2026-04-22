def test_widget_created_directly_on_form_block(self):
        """Test that a widget can be created directly on a form block."""

        form = st.form("form")
        form.checkbox("widget")

        self.assertEqual("form", self._get_last_checkbox_form_id())