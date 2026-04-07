def test_cache_fragment_cache(self):
        """
        When a cache called "template_fragments" is present, the cache tag
        will use it in preference to 'default'
        """
        t1 = self.engine.from_string(
            "{% load cache %}{% cache 1 fragment %}foo{% endcache %}"
        )
        t2 = self.engine.from_string(
            '{% load cache %}{% cache 1 fragment using="default" %}bar{% endcache %}'
        )

        ctx = Context()
        o1 = t1.render(ctx)
        o2 = t2.render(ctx)

        self.assertEqual(o1, "foo")
        self.assertEqual(o2, "bar")