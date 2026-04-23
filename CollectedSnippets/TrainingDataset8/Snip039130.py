def test_inside_column(self):
        """Test that it works correctly inside of a column."""
        col1, col2 = st.columns([3, 2])

        with col1:
            st.time_input("foo")

        all_deltas = self.get_all_deltas_from_queue()

        # 4 elements will be created: 1 horizontal block, 2 columns, 1 widget
        self.assertEqual(len(all_deltas), 4)
        time_input_proto = self.get_delta_from_queue().new_element.time_input

        self.assertEqual(time_input_proto.label, "foo")