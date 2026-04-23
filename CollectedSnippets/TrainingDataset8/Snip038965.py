def test_metric_in_column(self):
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Column 1", 123, 123)
        with col2:
            st.metric("Column 2", 123, 123)
        with col3:
            st.metric("Column 3", 123, 123)
        col4.metric("Column 4", -123, -123)
        col5.metric("Column 5", "-123", 0)

        all_deltas = self.get_all_deltas_from_queue()

        # 11 elements will be created: 1 horizontal block, 5 columns, 5 widget
        self.assertEqual(len(all_deltas), 11)
        metric_proto = self.get_delta_from_queue().new_element.metric

        self.assertEqual(metric_proto.label, "Column 5")