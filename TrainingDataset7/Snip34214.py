def test_resolve_on_context_method(self):
        """
        #17778 -- Variable shouldn't resolve RequestContext methods
        """
        empty_context = Context()

        with self.assertRaises(VariableDoesNotExist):
            Variable("no_such_variable").resolve(empty_context)

        with self.assertRaises(VariableDoesNotExist):
            Variable("new").resolve(empty_context)

        self.assertEqual(
            Variable("new").resolve(Context({"new": "foo"})),
            "foo",
        )