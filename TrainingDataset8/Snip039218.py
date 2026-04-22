def test_label_required(self):
        """Test that label is required"""
        with self.assertRaises(TypeError):
            st.expander()