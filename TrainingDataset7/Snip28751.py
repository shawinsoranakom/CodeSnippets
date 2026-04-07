def test_inheritance_resolve_columns(self):
        Restaurant.objects.create(
            name="Bobs Cafe",
            address="Somewhere",
            serves_pizza=True,
            serves_hot_dogs=True,
        )
        p = Place.objects.select_related("restaurant")[0]
        self.assertIsInstance(p.restaurant.serves_pizza, bool)