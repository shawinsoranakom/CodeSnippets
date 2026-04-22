def test_equal_width_columns(self):
        """Test that it works correctly when spec is int"""
        columns = st.columns(3)

        for column in columns:
            with column:
                st.write("Hello")

        all_deltas = self.get_all_deltas_from_queue()

        columns_blocks = all_deltas[1:4]
        # 7 elements will be created: 1 horizontal block, 3 columns, 3 markdown
        self.assertEqual(len(all_deltas), 7)
        self.assertEqual(columns_blocks[0].add_block.column.weight, 1.0 / 3)
        self.assertEqual(columns_blocks[1].add_block.column.weight, 1.0 / 3)
        self.assertEqual(columns_blocks[2].add_block.column.weight, 1.0 / 3)