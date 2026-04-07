def setUpTestData(cls):
        cls.vw = Car.objects.create(name="VW")
        cls.bmw = Car.objects.create(name="BMW")
        cls.toyota = Car.objects.create(name="Toyota")

        cls.wheelset = Part.objects.create(name="Wheelset")
        cls.doors = Part.objects.create(name="Doors")
        cls.engine = Part.objects.create(name="Engine")
        cls.airbag = Part.objects.create(name="Airbag")
        cls.sunroof = Part.objects.create(name="Sunroof")

        cls.alice = Person.objects.create(name="Alice")
        cls.bob = Person.objects.create(name="Bob")
        cls.chuck = Person.objects.create(name="Chuck")
        cls.daisy = Person.objects.create(name="Daisy")