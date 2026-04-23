def test_with_many_vary_on(self):
        key = make_template_fragment_key("bar", ["abc", "def"])
        self.assertEqual(key, "template.cache.bar.17c1a507a0cb58384f4c639067a93520")