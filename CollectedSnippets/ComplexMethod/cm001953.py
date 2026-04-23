def test_product_index(self):
        _, row_index, col_index = self._prepare_tables()
        cell_index = ProductIndexMap(row_index, col_index)
        row_index_proj = cell_index.project_outer(cell_index)
        col_index_proj = cell_index.project_inner(cell_index)

        ind = cell_index.indices
        self.assertEqual(cell_index.num_segments, 9)

        # Projections should give back the original indices.
        np.testing.assert_array_equal(row_index.indices.numpy(), row_index_proj.indices.numpy())
        self.assertEqual(row_index.num_segments, row_index_proj.num_segments)
        self.assertEqual(row_index.batch_dims, row_index_proj.batch_dims)
        np.testing.assert_array_equal(col_index.indices.numpy(), col_index_proj.indices.numpy())
        self.assertEqual(col_index.batch_dims, col_index_proj.batch_dims)

        # The first and second "column" are identified in the first table.
        for i in range(3):
            self.assertEqual(ind[0, i, 0], ind[0, i, 1])
            self.assertNotEqual(ind[0, i, 0], ind[0, i, 2])

        # All rows are distinct in the first table.
        for i, i_2 in zip(range(3), range(3)):
            for j, j_2 in zip(range(3), range(3)):
                if i != i_2 and j != j_2:
                    self.assertNotEqual(ind[0, i, j], ind[0, i_2, j_2])

        # All cells are distinct in the second table.
        for i, i_2 in zip(range(3), range(3)):
            for j, j_2 in zip(range(3), range(3)):
                if i != i_2 or j != j_2:
                    self.assertNotEqual(ind[1, i, j], ind[1, i_2, j_2])