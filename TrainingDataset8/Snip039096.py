def test_max_min(self):
        ret = st.slider("Slider label", 101, 100, 101)
        c = self.get_delta_from_queue().new_element.slider

        self.assertEqual(ret, 101),
        self.assertEqual(c.min, 100)
        self.assertEqual(c.max, 101)