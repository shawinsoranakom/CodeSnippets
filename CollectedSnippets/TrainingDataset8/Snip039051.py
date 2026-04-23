def test_invalid_values(self, value, options):
        """Test that it raises an error on invalid value"""
        with pytest.raises(ValueError):
            st.select_slider("the label", value=value, options=options)