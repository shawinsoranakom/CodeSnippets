def test_value_smaller_than_max(self):
        ret = st.slider("Slider label", 10, 100, 101)
        c = self.get_delta_from_queue().new_element.slider

        self.assertEqual(ret, 101)
        self.assertEqual(c.max, 101)