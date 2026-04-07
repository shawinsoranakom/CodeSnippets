def test_clone(self):
        index = models.Index(fields=["title"])
        new_index = index.clone()
        self.assertIsNot(index, new_index)
        self.assertEqual(index.fields, new_index.fields)