def test_nested_wrapper_invoked(self):
        outer_wrapper = self.mock_wrapper()
        inner_wrapper = self.mock_wrapper()
        with (
            connection.execute_wrapper(outer_wrapper),
            connection.execute_wrapper(inner_wrapper),
        ):
            self.call_execute(connection)
            self.assertEqual(inner_wrapper.call_count, 1)
            self.call_executemany(connection)
            self.assertEqual(inner_wrapper.call_count, 2)