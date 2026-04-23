def setUpTestData(cls):
        cls.o1 = OrgUnit.objects.create(name="o1")
        cls.o2 = OrgUnit.objects.create(name="o2")
        cls.l1 = Login.objects.create(description="l1", orgunit=cls.o1)
        cls.l2 = Login.objects.create(description="l2", orgunit=cls.o2)