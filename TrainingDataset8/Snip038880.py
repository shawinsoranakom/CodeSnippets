def test_deltas_that_melt_dataframes(self):
        """Some element types require that their dataframes are
        'melted' (https://pandas.pydata.org/docs/reference/api/pandas.melt.html)
         before being sent to the frontend. Test that the melting occurs.
        """
        deltas = self._get_deltas_that_melt_dataframes()

        for delta in deltas:
            el = delta(DATAFRAME)
            el._legacy_add_rows(NEW_ROWS)

            df_proto = _get_data_frame(self.get_delta_from_queue())

            # Test that the add_rows delta is properly melted
            rows = df_proto.data.cols[0].int64s.data
            self.assertEqual([2, 3, 4, 2, 3, 4], rows)