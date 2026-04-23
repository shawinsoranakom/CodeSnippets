def test_cache_missing_backend(self):
        """
        When a cache that doesn't exist is specified, the cache tag will
        raise a TemplateSyntaxError
        '"""
        t = self.engine.from_string(
            '{% load cache %}{% cache 1 backend using="unknown" %}bar{% endcache %}'
        )

        ctx = Context()
        with self.assertRaises(TemplateSyntaxError):
            t.render(ctx)