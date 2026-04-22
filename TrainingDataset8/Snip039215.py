def test_columns_with_default_small_gap(self):
        """Test that it works correctly with no gap argument (gap size is default of small)"""

        st.columns(3)

        all_deltas = self.get_all_deltas_from_queue()

        horizontal_block = all_deltas[0]
        columns_blocks = all_deltas[1:4]

        # 4 elements will be created: 1 horizontal block, 3 columns, each receives "small" gap arg
        self.assertEqual(len(all_deltas), 4)
        self.assertEqual(horizontal_block.add_block.horizontal.gap, "small")
        self.assertEqual(columns_blocks[0].add_block.column.gap, "small")
        self.assertEqual(columns_blocks[1].add_block.column.gap, "small")
        self.assertEqual(columns_blocks[2].add_block.column.gap, "small")