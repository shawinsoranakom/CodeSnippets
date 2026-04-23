def test_st_legacy_table(self):
        """Test st._legacy_table."""
        df = pd.DataFrame([[1, 2], [3, 4]], columns=["col1", "col2"])

        st._legacy_table(df)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.table.data.cols[0].int64s.data, [1, 3])
        self.assertEqual(el.table.data.cols[1].int64s.data, [2, 4])
        self.assertEqual(
            el.table.columns.plain_index.data.strings.data, ["col1", "col2"]
        )