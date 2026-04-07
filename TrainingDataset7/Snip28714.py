def test_values_works_on_parent_model_fields(self):
        # The values() command also works on fields from parent models.
        self.assertSequenceEqual(
            ItalianRestaurant.objects.values("name", "rating"),
            [
                {"rating": 4, "name": "Ristorante Miron"},
            ],
        )