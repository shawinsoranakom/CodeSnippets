def test_simple_legacy_add_rows_with_clear_queue(self):
        """Test plain old _legacy_add_rows after clearing the queue."""
        all_methods = self._get_unnamed_data_methods() + self._get_named_data_methods()

        for method in all_methods:
            # Create a new data-carrying element (e.g. st._legacy_dataframe)
            el = method(DATAFRAME)

            # Make sure it has 2 rows in it.
            df_proto = _get_data_frame(self.get_delta_from_queue())
            num_rows = len(df_proto.data.cols[0].int64s.data)
            self.assertEqual(2, num_rows)

            # This is what we're testing:
            self.forward_msg_queue.clear()
            el._legacy_add_rows(NEW_ROWS)

            # Make sure there are 3 rows in the delta that got appended.
            ar = self.get_delta_from_queue().add_rows
            num_rows = len(ar.data.data.cols[0].int64s.data)
            self.assertEqual(3, num_rows)

            # Clear the queue so the next loop is like a brand new test.
            get_script_run_ctx().reset()
            self.forward_msg_queue.clear()