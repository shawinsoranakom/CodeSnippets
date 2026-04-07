def setUpTestData(cls):
        cls.t1 = Tag.objects.create(name="t1")
        cls.t2 = Tag.objects.create(name="t2", parent=cls.t1)
        cls.t3 = Tag.objects.create(name="t3", parent=cls.t1)
        cls.t4 = Tag.objects.create(name="t4", parent=cls.t3)
        cls.t5 = Tag.objects.create(name="t5", parent=cls.t3)

        cls.p1_o1 = Staff.objects.create(id=1, name="p1", organisation="o1")
        cls.p2_o1 = Staff.objects.create(id=2, name="p2", organisation="o1")
        cls.p3_o1 = Staff.objects.create(id=3, name="p3", organisation="o1")
        cls.p1_o2 = Staff.objects.create(id=4, name="p1", organisation="o2")
        cls.p1_o1.coworkers.add(cls.p2_o1, cls.p3_o1)
        cls.st1 = StaffTag.objects.create(staff=cls.p1_o1, tag=cls.t1)
        StaffTag.objects.create(staff=cls.p1_o1, tag=cls.t1)

        cls.celeb1 = Celebrity.objects.create(name="c1")
        cls.celeb2 = Celebrity.objects.create(name="c2")

        cls.fan1 = Fan.objects.create(fan_of=cls.celeb1)
        cls.fan2 = Fan.objects.create(fan_of=cls.celeb1)
        cls.fan3 = Fan.objects.create(fan_of=cls.celeb2)