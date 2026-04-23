def test_with_unicode_vary_on(self):
        key = make_template_fragment_key("foo", ["42º", "😀"])
        self.assertEqual(key, "template.cache.foo.7ced1c94e543668590ba39b3c08b0237")