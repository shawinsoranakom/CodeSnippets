def test_count(self):
        self.assertEqual(self.curry.ingredients.count(), 3)
        self.assertEqual(self.tomato.recipes.count(), 1)