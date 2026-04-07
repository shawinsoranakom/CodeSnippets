def test_clone_with_expressions(self):
        index = models.Index(Upper("title"), name="book_func_idx")
        new_index = index.clone()
        self.assertIsNot(index, new_index)
        self.assertEqual(index.expressions, new_index.expressions)