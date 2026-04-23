def test_constructor(self):
        """
        The constructor is correctly distinguishing between usage of
        CacheMiddleware as Middleware vs. usage of CacheMiddleware as view
        decorator and setting attributes appropriately.
        """
        # If only one argument is passed in construction, it's being used as
        # middleware.
        middleware = CacheMiddleware(empty_response)

        # Now test object attributes against values defined in setUp above
        self.assertEqual(middleware.cache_timeout, 30)
        self.assertEqual(middleware.key_prefix, "middlewareprefix")
        self.assertEqual(middleware.cache_alias, "other")
        self.assertEqual(middleware.cache, self.other_cache)

        # If more arguments are being passed in construction, it's being used
        # as a decorator. First, test with "defaults":
        as_view_decorator = CacheMiddleware(
            empty_response, cache_alias=None, key_prefix=None
        )

        self.assertEqual(
            as_view_decorator.cache_timeout, 30
        )  # Timeout value for 'default' cache, i.e. 30
        self.assertEqual(as_view_decorator.key_prefix, "")
        # Value of DEFAULT_CACHE_ALIAS from django.core.cache
        self.assertEqual(as_view_decorator.cache_alias, "default")
        self.assertEqual(as_view_decorator.cache, self.default_cache)

        # Next, test with custom values:
        as_view_decorator_with_custom = CacheMiddleware(
            hello_world_view, cache_timeout=60, cache_alias="other", key_prefix="foo"
        )

        self.assertEqual(as_view_decorator_with_custom.cache_timeout, 60)
        self.assertEqual(as_view_decorator_with_custom.key_prefix, "foo")
        self.assertEqual(as_view_decorator_with_custom.cache_alias, "other")
        self.assertEqual(as_view_decorator_with_custom.cache, self.other_cache)