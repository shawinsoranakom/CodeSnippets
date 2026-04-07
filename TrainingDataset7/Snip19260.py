def test_without_vary_on(self):
        key = make_template_fragment_key("a.fragment")
        self.assertEqual(
            key, "template.cache.a.fragment.d41d8cd98f00b204e9800998ecf8427e"
        )