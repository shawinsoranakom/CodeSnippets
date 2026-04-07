def setUpTestData(cls):
        generic = NamedCategory.objects.create(name="Generic")
        cls.t1 = Tag.objects.create(name="t1", category=generic)

        n1 = Note.objects.create(note="n1", misc="foo")
        n2 = Note.objects.create(note="n2", misc="bar")

        e1 = ExtraInfo.objects.create(info="e1", note=n1)
        e2 = ExtraInfo.objects.create(info="e2", note=n2)

        cls.a1 = Author.objects.create(name="a1", num=1001, extra=e1)
        cls.a3 = Author.objects.create(name="a3", num=3003, extra=e2)

        cls.r1 = Report.objects.create(name="r1", creator=cls.a1)
        cls.r2 = Report.objects.create(name="r2", creator=cls.a3)
        cls.r3 = Report.objects.create(name="r3")

        cls.i1 = Item.objects.create(
            name="i1", created=datetime.datetime.now(), note=n1, creator=cls.a1
        )
        cls.i2 = Item.objects.create(
            name="i2", created=datetime.datetime.now(), note=n1, creator=cls.a3
        )