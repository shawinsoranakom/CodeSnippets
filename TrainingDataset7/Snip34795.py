def test_contextlist_keys(self):
        c1 = Context()
        c1.update({"hello": "world", "goodbye": "john"})
        c1.update({"hello": "dolly", "dolly": "parton"})
        c2 = Context()
        c2.update({"goodbye": "world", "python": "rocks"})
        c2.update({"goodbye": "dolly"})

        k = ContextList([c1, c2])
        # None, True and False are builtins of BaseContext, and present
        # in every Context without needing to be added.
        self.assertEqual(
            {"None", "True", "False", "hello", "goodbye", "python", "dolly"}, k.keys()
        )