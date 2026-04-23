def test_iteration_unrendered(self):
        # unrendered response raises an exception on iteration
        response = self._response()
        self.assertFalse(response.is_rendered)

        def iteration():
            list(response)

        msg = "The response content must be rendered before it can be iterated over."
        with self.assertRaisesMessage(ContentNotRenderedError, msg):
            iteration()
        self.assertFalse(response.is_rendered)