def test_filter_inherited_model(self):
        self.assertQuerySetEqual(
            ItalianRestaurant.objects.filter(address="1234 W. Ash"),
            [
                "Ristorante Miron",
            ],
            attrgetter("name"),
        )