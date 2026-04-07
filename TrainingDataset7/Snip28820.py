def test_no_default_related_name(self):
        self.assertEqual(list(self.author.editor_set.all()), [self.editor])