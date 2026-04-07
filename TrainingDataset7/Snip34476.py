def test_iteration_rendered(self):
        # iteration works for rendered responses
        response = self._response().render()
        self.assertEqual(list(response), [b"foo"])