def test_wrapper_invoked(self):
        wrapper = self.mock_wrapper()
        with connection.execute_wrapper(wrapper):
            self.call_execute(connection)
        self.assertTrue(wrapper.called)
        (_, sql, params, many, context), _ = wrapper.call_args
        self.assertIn("SELECT", sql)
        self.assertIsNone(params)
        self.assertIs(many, False)
        self.assertEqual(context["connection"], connection)