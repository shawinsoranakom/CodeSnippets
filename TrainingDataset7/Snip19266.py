def test_long_vary_on(self):
        key = make_template_fragment_key("foo", ["x" * 10000])
        self.assertEqual(key, "template.cache.foo.3670b349b5124aa56bdb50678b02b23a")