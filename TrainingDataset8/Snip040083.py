def test_st_legacy_dataframe(self):
        """Test st._legacy_dataframe."""
        df = pd.DataFrame({"one": [1, 2], "two": [11, 22]})

        st._legacy_dataframe(df)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.data_frame.data.cols[0].int64s.data, [1, 2])
        self.assertEqual(
            el.data_frame.columns.plain_index.data.strings.data, ["one", "two"]
        )