def test_numpy_array_with_value(self):
        """Test that it can be called with options=numpy array"""
        st.select_slider("the label", value=3, options=np.array([1, 2, 3, 4]))

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [2])