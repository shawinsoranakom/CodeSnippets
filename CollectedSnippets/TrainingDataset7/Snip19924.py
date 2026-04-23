def test_get_for_concrete_model(self):
        """
        Make sure the `for_concrete_model` kwarg correctly works
        with concrete, proxy and deferred models
        """
        concrete_model_ct = ContentType.objects.get_for_model(ConcreteModel)
        self.assertEqual(
            concrete_model_ct, ContentType.objects.get_for_model(ProxyModel)
        )
        self.assertEqual(
            concrete_model_ct,
            ContentType.objects.get_for_model(ConcreteModel, for_concrete_model=False),
        )

        proxy_model_ct = ContentType.objects.get_for_model(
            ProxyModel, for_concrete_model=False
        )
        self.assertNotEqual(concrete_model_ct, proxy_model_ct)

        # Make sure deferred model are correctly handled
        ConcreteModel.objects.create(name="Concrete")
        DeferredConcreteModel = ConcreteModel.objects.only("pk").get().__class__
        DeferredProxyModel = ProxyModel.objects.only("pk").get().__class__

        self.assertEqual(
            concrete_model_ct, ContentType.objects.get_for_model(DeferredConcreteModel)
        )
        self.assertEqual(
            concrete_model_ct,
            ContentType.objects.get_for_model(
                DeferredConcreteModel, for_concrete_model=False
            ),
        )
        self.assertEqual(
            concrete_model_ct, ContentType.objects.get_for_model(DeferredProxyModel)
        )
        self.assertEqual(
            proxy_model_ct,
            ContentType.objects.get_for_model(
                DeferredProxyModel, for_concrete_model=False
            ),
        )