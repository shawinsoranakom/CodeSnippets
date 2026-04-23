def test_parent_fields_available_for_filtering_in_child_model(self):
        # Parent fields can be used directly in filters on the child model.
        self.assertQuerySetEqual(
            Restaurant.objects.filter(name="Demon Dogs"),
            [
                "Demon Dogs",
            ],
            attrgetter("name"),
        )
        self.assertQuerySetEqual(
            ItalianRestaurant.objects.filter(address="1234 W. Ash"),
            [
                "Ristorante Miron",
            ],
            attrgetter("name"),
        )