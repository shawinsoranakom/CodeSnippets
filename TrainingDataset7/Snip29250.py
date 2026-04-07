def setUpTestData(cls):
        cls.p1 = Place.objects.create(name="Demon Dogs", address="944 W. Fullerton")
        cls.p2 = Place.objects.create(name="Ace Hardware", address="1013 N. Ashland")
        cls.r1 = Restaurant.objects.create(
            place=cls.p1, serves_hot_dogs=True, serves_pizza=False
        )
        cls.b1 = Bar.objects.create(place=cls.p1, serves_cocktails=False)