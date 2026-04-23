def test_legacy_add_rows_suceeds_when_wrong_shape(self):
        """_legacy_add_rows doesn't raise an error even if its input has the
        wrong shape. Instead, it's up to the frontend to catch and raise
        this error.
        """
        all_methods = self._get_unnamed_data_methods() + self._get_named_data_methods()

        for method in all_methods:
            # Create a new data-carrying element (e.g. st._legacy_dataframe)
            el = method(DATAFRAME)

            # This is what we're testing:
            el._legacy_add_rows(NEW_ROWS_WRONG_SHAPE)

            # Clear the queue so the next loop is like a brand new test.
            get_script_run_ctx().reset()
            self.forward_msg_queue.clear()