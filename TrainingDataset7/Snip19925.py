def test_get_for_concrete_models(self):
        """
        Make sure the `for_concrete_models` kwarg correctly works
        with concrete, proxy and deferred models.
        """
        concrete_model_ct = ContentType.objects.get_for_model(ConcreteModel)

        cts = ContentType.objects.get_for_models(ConcreteModel, ProxyModel)
        self.assertEqual(
            cts,
            {
                ConcreteModel: concrete_model_ct,
                ProxyModel: concrete_model_ct,
            },
        )

        proxy_model_ct = ContentType.objects.get_for_model(
            ProxyModel, for_concrete_model=False
        )
        cts = ContentType.objects.get_for_models(
            ConcreteModel, ProxyModel, for_concrete_models=False
        )
        self.assertEqual(
            cts,
            {
                ConcreteModel: concrete_model_ct,
                ProxyModel: proxy_model_ct,
            },
        )

        # Make sure deferred model are correctly handled
        ConcreteModel.objects.create(name="Concrete")
        DeferredConcreteModel = ConcreteModel.objects.only("pk").get().__class__
        DeferredProxyModel = ProxyModel.objects.only("pk").get().__class__

        cts = ContentType.objects.get_for_models(
            DeferredConcreteModel, DeferredProxyModel
        )
        self.assertEqual(
            cts,
            {
                DeferredConcreteModel: concrete_model_ct,
                DeferredProxyModel: concrete_model_ct,
            },
        )

        cts = ContentType.objects.get_for_models(
            DeferredConcreteModel, DeferredProxyModel, for_concrete_models=False
        )
        self.assertEqual(
            cts,
            {
                DeferredConcreteModel: concrete_model_ct,
                DeferredProxyModel: proxy_model_ct,
            },
        )