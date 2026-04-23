def test_per_thread(self):
        """The cache instance is different for each thread."""
        thread_caches = []
        middleware = CacheMiddleware(empty_response)

        def runner():
            thread_caches.append(middleware.cache)

        for _ in range(2):
            thread = threading.Thread(target=runner)
            thread.start()
            thread.join()

        self.assertIsNot(thread_caches[0], thread_caches[1])