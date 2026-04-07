def test_with_ints_vary_on(self):
        key = make_template_fragment_key("foo", [1, 2, 3, 4, 5])
        self.assertEqual(key, "template.cache.foo.7ae8fd2e0d25d651c683bdeebdb29461")