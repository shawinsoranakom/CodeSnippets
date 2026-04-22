def test_numpy_array_no_value(self):
        """Test that it can be called with options=numpy array, no value"""
        st.select_slider("the label", options=np.array([1, 2, 3, 4]))

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [0])