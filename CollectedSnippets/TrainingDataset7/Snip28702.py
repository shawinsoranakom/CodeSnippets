def setUpTestData(cls):
        cls.restaurant = Restaurant.objects.create(
            name="Demon Dogs",
            address="944 W. Fullerton",
            serves_hot_dogs=True,
            serves_pizza=False,
            rating=2,
        )

        chef = Chef.objects.create(name="Albert")
        cls.italian_restaurant = ItalianRestaurant.objects.create(
            name="Ristorante Miron",
            address="1234 W. Ash",
            serves_hot_dogs=False,
            serves_pizza=False,
            serves_gnocchi=True,
            rating=4,
            chef=chef,
        )