def test_legacy_add_rows_works_when_new_name(self):
        """Test _legacy_add_rows with new named datasets."""

        for method in self._get_named_data_methods():
            # Create a new data-carrying element (e.g. st._legacy_dataframe)
            el = method(DATAFRAME)
            self.forward_msg_queue.clear()

            # This is what we're testing:
            el._legacy_add_rows(new_name=NEW_ROWS)

            # Make sure there are 3 rows in the delta that got appended.
            ar = self.get_delta_from_queue().add_rows
            num_rows = len(ar.data.data.cols[0].int64s.data)
            self.assertEqual(3, num_rows)

            # Clear the queue so the next loop is like a brand new test.
            get_script_run_ctx().reset()
            self.forward_msg_queue.clear()