def test_noneType_option(self):
        """Test NoneType option value."""
        current_value = st.radio("the label", (None, "selected"), 0)

        self.assertEqual(current_value, None)