def test_not_equal_width_float_columns(self):
        """Test that it works correctly when spec is list of floats or ints"""
        weights = [7.5, 2.5, 5]
        sum_weights = sum(weights)
        columns = st.columns(weights)

        for column in columns:
            with column:
                pass

        all_deltas = self.get_all_deltas_from_queue()

        columns_blocks = all_deltas[1:]
        # 4 elements will be created: 1 horizontal block, 3 columns
        self.assertEqual(len(all_deltas), 4)
        self.assertEqual(len(columns_blocks), 3)
        self.assertEqual(columns_blocks[0].add_block.column.weight, 7.5 / sum_weights)
        self.assertEqual(columns_blocks[1].add_block.column.weight, 2.5 / sum_weights)
        self.assertEqual(columns_blocks[2].add_block.column.weight, 5.0 / sum_weights)