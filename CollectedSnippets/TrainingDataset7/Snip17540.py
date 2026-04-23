def tearDown(self):
        # The get_group_permissions test messes with ContentTypes, which will
        # be cached; flush the cache to ensure there are no side effects
        # Refs #14975, #14925
        ContentType.objects.clear_cache()