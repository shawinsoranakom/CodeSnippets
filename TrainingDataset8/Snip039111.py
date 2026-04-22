def test_inside_column(self):
        """Test that it works correctly inside of a column."""
        col1, col2, col3 = st.columns([2.5, 1.5, 8.3])

        with col1:
            st.text_area("foo")

        all_deltas = self.get_all_deltas_from_queue()

        # 5 elements will be created: 1 horizontal block, 3 columns, 1 widget
        self.assertEqual(len(all_deltas), 5)
        text_area_proto = self.get_delta_from_queue().new_element.text_area

        self.assertEqual(text_area_proto.label, "foo")