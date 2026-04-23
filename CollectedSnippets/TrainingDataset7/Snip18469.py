def test_wrapper_connection_specific(self):
        wrapper = self.mock_wrapper()
        with connections["other"].execute_wrapper(wrapper):
            self.assertEqual(connections["other"].execute_wrappers, [wrapper])
            self.call_execute(connection)
        self.assertFalse(wrapper.called)
        self.assertEqual(connection.execute_wrappers, [])
        self.assertEqual(connections["other"].execute_wrappers, [])