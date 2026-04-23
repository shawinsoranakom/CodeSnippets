def test_max_selections(self):
        st.multiselect("the label", ("m", "f"), max_selections=2)

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.max_selections, 2)