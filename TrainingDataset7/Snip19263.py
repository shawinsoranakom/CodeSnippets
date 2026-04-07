def test_proper_escaping(self):
        key = make_template_fragment_key("spam", ["abc:def%"])
        self.assertEqual(key, "template.cache.spam.06c8ae8e8c430b69fb0a6443504153dc")