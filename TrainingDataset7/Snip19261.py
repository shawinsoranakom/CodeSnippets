def test_with_one_vary_on(self):
        key = make_template_fragment_key("foo", ["abc"])
        self.assertEqual(key, "template.cache.foo.493e283d571a73056196f1a68efd0f66")