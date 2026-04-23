def setUpTestData(cls):
        cls.jim_douglas = Person.objects.create(name="Jim Douglas")
        cls.car = Car.objects.create(name="1963 Volkswagen Beetle")
        cls.herbie = cls.jim_douglas.possessed_cars.create(
            car=cls.car,
            belongs_to=cls.jim_douglas,
        )

        cls.person_binary = Person.objects.create(name="Person", data=b"binary data")
        cls.person_binary_get = Person.objects.get(pk=cls.person_binary.pk)