def setUpTestData(cls):
        cls.oa = ObjectA.objects.create(name="oa")
        cls.poa = ProxyObjectA.objects.get(name="oa")
        cls.coa = ChildObjectA.objects.create(name="coa")
        cls.wrong_type = Order.objects.create(id=cls.oa.pk)
        cls.ob = ObjectB.objects.create(name="ob", objecta=cls.oa, num=1)
        cls.pob1 = ProxyObjectB.objects.create(name="pob", objecta=cls.oa, num=2)
        cls.pob = ProxyObjectB.objects.all()
        cls.c = ObjectC.objects.create(childobjecta=cls.coa)