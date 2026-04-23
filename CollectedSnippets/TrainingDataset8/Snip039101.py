def test_inside_column(self):
        """Test that it works correctly inside of a column."""
        col1, col2 = st.columns(2)

        with col1:
            st.slider("foo")

        all_deltas = self.get_all_deltas_from_queue()

        # 4 elements will be created: 1 horizontal block, 2 columns, 1 widget
        self.assertEqual(len(all_deltas), 4)
        slider_proto = self.get_delta_from_queue().new_element.slider

        self.assertEqual(slider_proto.label, "foo")