def test_incr_write_connection(self):
        cache.set("number", 42)
        with mock.patch(
            "django.core.cache.backends.redis.RedisCacheClient.get_client"
        ) as mocked_get_client:
            cache.incr("number")
            self.assertEqual(mocked_get_client.call_args.kwargs, {"write": True})