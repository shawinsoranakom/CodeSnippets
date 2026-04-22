def test_format_function(self):
        """Test that it formats options."""
        arg_options = [{"name": "john", "height": 180}, {"name": "lisa", "height": 200}]
        proto_options = ["john", "lisa"]

        st.multiselect("the label", arg_options, format_func=lambda x: x["name"])

        c = self.get_delta_from_queue().new_element.multiselect
        self.assertEqual(c.label, "the label")
        self.assertListEqual(c.default[:], [])
        self.assertEqual(c.options, proto_options)