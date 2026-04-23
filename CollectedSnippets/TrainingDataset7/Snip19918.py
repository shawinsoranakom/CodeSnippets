def test_get_for_models_empty_cache(self):
        # Empty cache.
        with self.assertNumQueries(1):
            cts = ContentType.objects.get_for_models(
                ContentType, FooWithUrl, ProxyModel, ConcreteModel
            )
        self.assertEqual(
            cts,
            {
                ContentType: ContentType.objects.get_for_model(ContentType),
                FooWithUrl: ContentType.objects.get_for_model(FooWithUrl),
                ProxyModel: ContentType.objects.get_for_model(ProxyModel),
                ConcreteModel: ContentType.objects.get_for_model(ConcreteModel),
            },
        )