def setUpTestData(cls):
        cls.d1 = ModelD.objects.create(name="foo")
        d2 = ModelD.objects.create(name="bar")
        cls.a1 = ModelA.objects.create(name="a1", d=cls.d1)
        c = ModelC.objects.create(name="c")
        b = ModelB.objects.create(name="b", c=c)
        cls.a2 = ModelA.objects.create(name="a2", b=b, d=d2)