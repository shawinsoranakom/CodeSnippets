def test_response_raises_multi_arg_exception(self):
        """A request may raise an exception with more than one required arg."""
        with self.assertRaises(TwoArgException) as cm:
            self.client.get("/two_arg_exception/")
        self.assertEqual(cm.exception.args, ("one", "two"))