def test_retrieval(self):
        # Forward retrieval
        self.assertSequenceEqual(
            self.curry.ingredients.all(), [self.pea, self.potato, self.tomato]
        )
        # Backward retrieval
        self.assertEqual(self.tomato.recipes.get(), self.curry)