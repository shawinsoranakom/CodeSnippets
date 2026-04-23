def test_variable_columns(self):
        weights = [3, 1, 4, 1, 5, 9]
        sum_weights = sum(weights)
        st.columns(weights)

        for i, w in enumerate(weights):
            # Pull the delta from the back of the queue, using negative index
            delta = self.get_delta_from_queue(i - len(weights))
            self.assertEqual(delta.add_block.column.weight, w / sum_weights)