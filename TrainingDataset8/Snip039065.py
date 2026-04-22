def test_pandas_series_with_invalid_value(self):
        """Test that it raises an error on invalid value"""
        with pytest.raises(ValueError):
            st.select_slider(
                "the label", value=10, options=pd.Series([1, 2, 3, 4, 5, 6])
            )