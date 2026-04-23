def test_numpy_array_with_range(self):
        """Test that it can be called with options=numpy array, value=range"""
        st.select_slider(
            "the label", value=(2, 5), options=np.array([1, 2, 3, 4, 5, 6])
        )

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [1, 4])