def test_pandas_series_with_value(self):
        """Test that it can be called with options=pandas series"""
        st.select_slider("the label", value=3, options=pd.Series([1, 2, 3, 4, 5]))

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [2])