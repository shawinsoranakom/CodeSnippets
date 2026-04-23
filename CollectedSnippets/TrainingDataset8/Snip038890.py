def test_legacy_add_rows_with_pyarrow_table_data(self):
        """Test that an error is raised when called with `pyarrow.Table` data."""
        all_methods = self._get_unnamed_data_methods() + self._get_named_data_methods()

        for method in all_methods:
            with self.assertRaises(StreamlitAPIException):
                # Create a new data-carrying element (e.g. st._legacy_dataframe)
                el = method(DATAFRAME)
                # This is what we're testing:
                el._legacy_add_rows(pa.Table.from_pandas(NEW_ROWS))

            # Clear the queue so the next loop is like a brand new test.
            get_script_run_ctx().reset()
            self.forward_msg_queue.clear()