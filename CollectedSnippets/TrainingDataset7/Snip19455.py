def test_template_tags_with_different_name(self):
        self.assertEqual(self._check_engines(engines.all()), [])