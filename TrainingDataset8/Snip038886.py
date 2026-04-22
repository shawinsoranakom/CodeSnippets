def test_named_legacy_add_rows(self):
        """Test _legacy_add_rows with a named dataset."""
        for method in self._get_named_data_methods():
            # Create a new data-carrying element (e.g. st._legacy_dataframe)
            el = method(DATAFRAME)

            # Make sure it has 2 rows in it.
            df_proto = _get_data_frame(self.get_delta_from_queue())
            num_rows = len(df_proto.data.cols[0].int64s.data)
            self.assertEqual(2, num_rows)

            # This is what we're testing:
            el._legacy_add_rows(mydata1=NEW_ROWS)

            # Make sure the add_rows proto looks like we expect
            df_proto = _get_data_frame(self.get_delta_from_queue(), name="mydata1")
            rows = df_proto.data.cols[0].int64s.data
            self.assertEqual([3, 4, 5], rows)

            # Clear the queue so the next loop is like a brand new test.
            get_script_run_ctx().reset()
            self.forward_msg_queue.clear()