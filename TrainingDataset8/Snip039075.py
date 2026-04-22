def test_not_iterable_option_types(self):
        """Test that it supports different types of options."""
        with pytest.raises(TypeError):
            st.selectbox("the label", 123)