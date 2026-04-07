def test_model_pickle_dynamic(self):
        class Meta:
            proxy = True

        dynclass = type(
            "DynamicEventSubclass",
            (Event,),
            {"Meta": Meta, "__module__": Event.__module__},
        )
        original = dynclass(pk=1)
        dumped = pickle.dumps(original)
        reloaded = pickle.loads(dumped)
        self.assertEqual(original, reloaded)
        self.assertIs(reloaded.__class__, dynclass)