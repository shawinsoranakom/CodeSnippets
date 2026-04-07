def test_can_get_items_using_index_and_slice_notation(self):
        self.assertEqual(self.get_ordered_articles()[0].name, "Article 1")
        self.assertSequenceEqual(
            self.get_ordered_articles()[1:3],
            [self.articles[1], self.articles[2]],
        )