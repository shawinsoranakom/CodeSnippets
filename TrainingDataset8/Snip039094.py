def test_value_greater_than_min(self):
        ret = st.slider("Slider label", 10, 100, 0)
        c = self.get_delta_from_queue().new_element.slider

        self.assertEqual(ret, 0)
        self.assertEqual(c.min, 0)