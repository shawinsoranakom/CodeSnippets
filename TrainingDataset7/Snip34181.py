def test_str(self):
        exc = VariableDoesNotExist(msg="Failed lookup in %r", params=({"foo": "bar"},))
        self.assertEqual(str(exc), "Failed lookup in {'foo': 'bar'}")