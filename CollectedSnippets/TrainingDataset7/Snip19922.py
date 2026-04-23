def test_get_for_models_full_cache(self):
        # Full cache
        ContentType.objects.get_for_model(ContentType)
        ContentType.objects.get_for_model(FooWithUrl)
        with self.assertNumQueries(0):
            cts = ContentType.objects.get_for_models(ContentType, FooWithUrl)
        self.assertEqual(
            cts,
            {
                ContentType: ContentType.objects.get_for_model(ContentType),
                FooWithUrl: ContentType.objects.get_for_model(FooWithUrl),
            },
        )