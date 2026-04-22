def test_pandas_series_no_value(self):
        """Test that it can be called with options=pandas series, no value"""
        st.select_slider("the label", options=pd.Series([1, 2, 3, 4, 5]))

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [0])