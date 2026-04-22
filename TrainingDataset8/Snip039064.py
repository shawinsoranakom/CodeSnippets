def test_pandas_series_with_range(self):
        """Test that it can be called with options=pandas series, value=range"""
        st.select_slider(
            "the label", value=(2, 5), options=pd.Series([1, 2, 3, 4, 5, 6])
        )

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [1, 4])