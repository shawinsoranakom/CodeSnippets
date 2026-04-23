def setUp(self):
        # The custom_perms test messes with ContentTypes, which will be cached.
        # Flush the cache to ensure there are no side effects.
        self.addCleanup(ContentType.objects.clear_cache)
        self.create_users()