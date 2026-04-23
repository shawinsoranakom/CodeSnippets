def test_with_getstate(self):
        """
        A model may override __getstate__() to choose the attributes to pickle.
        """

        class PickledModel(models.Model):
            def __getstate__(self):
                state = super().__getstate__().copy()
                del state["dont_pickle"]
                return state

        m = PickledModel()
        m.dont_pickle = 1
        dumped = pickle.dumps(m)
        self.assertEqual(m.dont_pickle, 1)
        reloaded = pickle.loads(dumped)
        self.assertFalse(hasattr(reloaded, "dont_pickle"))