def test_exists(self):
        self.assertTrue(self.curry.ingredients.exists())
        self.assertTrue(self.tomato.recipes.exists())