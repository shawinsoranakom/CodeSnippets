def test_querysets_required(self):
        msg = (
            "GenericPrefetch.__init__() missing 1 required "
            "positional argument: 'querysets'"
        )
        with self.assertRaisesMessage(TypeError, msg):
            GenericPrefetch("question")