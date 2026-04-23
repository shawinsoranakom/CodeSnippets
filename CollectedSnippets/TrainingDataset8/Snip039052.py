def test_invalid_options(self):
        """Test that it raises an error on an empty options"""
        with pytest.raises(StreamlitAPIException):
            st.select_slider("the label", options=[])