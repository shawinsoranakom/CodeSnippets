def test_update_inherited_model(self):
        self.italian_restaurant.address = "1234 W. Elm"
        self.italian_restaurant.save()
        self.assertQuerySetEqual(
            ItalianRestaurant.objects.filter(address="1234 W. Elm"),
            [
                "Ristorante Miron",
            ],
            attrgetter("name"),
        )