def test_deltas_that_melt_dataframes(self):
        deltas = self._get_deltas_that_melt_dataframes()

        for delta in deltas:
            element = delta(DATAFRAME)
            element._arrow_add_rows(NEW_ROWS)

            proto = bytes_to_data_frame(
                self.get_delta_from_queue().arrow_add_rows.data.data
            )

            pd.testing.assert_frame_equal(proto, MELTED_DATAFRAME)