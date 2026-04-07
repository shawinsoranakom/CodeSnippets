def test_get_for_models_creation(self):
        ContentType.objects.all().delete()
        with self.assertNumQueries(4):
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