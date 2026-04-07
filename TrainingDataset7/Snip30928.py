def test_model_pickle(self):
        """
        A model not defined on module level is picklable.
        """
        original = Container.SomeModel(pk=1)
        dumped = pickle.dumps(original)
        reloaded = pickle.loads(dumped)
        self.assertEqual(original, reloaded)
        # Also, deferred dynamic model works
        Container.SomeModel.objects.create(somefield=1)
        original = Container.SomeModel.objects.defer("somefield")[0]
        dumped = pickle.dumps(original)
        reloaded = pickle.loads(dumped)
        self.assertEqual(original, reloaded)
        self.assertEqual(original.somefield, reloaded.somefield)