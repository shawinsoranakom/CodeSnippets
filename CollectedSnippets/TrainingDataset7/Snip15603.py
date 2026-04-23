def setUpTestData(cls):
        cls.b1 = Band.objects.create(name="Pink Floyd", bio="", rank=1)
        cls.b2 = Band.objects.create(name="Foo Fighters", bio="", rank=5)