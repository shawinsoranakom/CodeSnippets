def test_inside_column(self):
        """Test that it works correctly inside of a column."""
        col1, col2, col3 = st.columns([2.5, 1.5, 0.5])

        with col1:
            st.text_input("foo")

        all_deltas = self.get_all_deltas_from_queue()

        # 5 elements will be created: 1 horizontal block, 3 columns, 1 widget
        self.assertEqual(len(all_deltas), 5)
        text_input_proto = self.get_delta_from_queue().new_element.text_input

        self.assertEqual(text_input_proto.label, "foo")