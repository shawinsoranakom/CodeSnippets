def test_naive_timelikes(self, value, return_value):
        """Ignore proto values (they change based on testing machine's timezone)"""
        ret = st.slider("the label", value=value)
        c = self.get_delta_from_queue().new_element.slider

        self.assertEqual(ret, return_value)
        self.assertEqual(c.label, "the label")