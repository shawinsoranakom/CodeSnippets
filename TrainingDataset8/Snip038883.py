def test_with_index_no_data_legacy_add_rows(self):
        """Test plain old _legacy_add_rows."""
        all_methods = self._get_unnamed_data_methods()

        for method in all_methods:
            # Create a new data-carrying element (e.g. st._legacy_dataframe)
            el = method(None)
            _get_data_frame(self.get_delta_from_queue())

            # This is what we're testing:
            el._legacy_add_rows(DATAFRAME_WITH_INDEX)

            # Make sure there are 2 rows in it now.
            df_proto = _get_data_frame(self.get_delta_from_queue())
            num_rows = len(df_proto.data.cols[0].int64s.data)
            self.assertEqual(2, num_rows)

            # Clear the queue so the next loop is like a brand new test.
            get_script_run_ctx().reset()
            self.forward_msg_queue.clear()