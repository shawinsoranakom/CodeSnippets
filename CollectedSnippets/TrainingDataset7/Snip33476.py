def test_cache_regression_20130(self):
        t = self.engine.from_string(
            "{% load cache %}{% cache 1 regression_20130 %}foo{% endcache %}"
        )
        cachenode = t.nodelist[1]
        self.assertEqual(cachenode.fragment_name, "regression_20130")