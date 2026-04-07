def test_cache_not_shared_between_managers(self):
        with self.assertNumQueries(1):
            ContentType.objects.get_for_model(ContentType)
        with self.assertNumQueries(0):
            ContentType.objects.get_for_model(ContentType)
        other_manager = ContentTypeManager()
        other_manager.model = ContentType
        with self.assertNumQueries(1):
            other_manager.get_for_model(ContentType)
        with self.assertNumQueries(0):
            other_manager.get_for_model(ContentType)