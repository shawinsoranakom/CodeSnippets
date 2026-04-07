def setUpTestData(cls):
        cls.nc1 = generic = NamedCategory.objects.create(name="Generic")
        cls.t1 = Tag.objects.create(name="t1", category=generic)
        cls.t2 = Tag.objects.create(name="t2", parent=cls.t1, category=generic)
        cls.t3 = Tag.objects.create(name="t3", parent=cls.t1)
        cls.t4 = Tag.objects.create(name="t4", parent=cls.t3)
        cls.t5 = Tag.objects.create(name="t5", parent=cls.t3)

        cls.n1 = Note.objects.create(note="n1", misc="foo", id=1)
        cls.n2 = Note.objects.create(note="n2", misc="bar", id=2)
        cls.n3 = Note.objects.create(note="n3", misc="foo", id=3, negate=False)

        cls.ann1 = Annotation.objects.create(name="a1", tag=cls.t1)
        cls.ann1.notes.add(cls.n1)
        ann2 = Annotation.objects.create(name="a2", tag=cls.t4)
        ann2.notes.add(cls.n2, cls.n3)

        # Create these out of order so that sorting by 'id' will be different
        # to sorting by 'info'. Helps detect some problems later.
        cls.e2 = ExtraInfo.objects.create(
            info="e2", note=cls.n2, value=41, filterable=False
        )
        e1 = ExtraInfo.objects.create(info="e1", note=cls.n1, value=42)

        cls.a1 = Author.objects.create(name="a1", num=1001, extra=e1)
        cls.a2 = Author.objects.create(name="a2", num=2002, extra=e1)
        cls.a3 = Author.objects.create(name="a3", num=3003, extra=cls.e2)
        cls.a4 = Author.objects.create(name="a4", num=4004, extra=cls.e2)

        cls.time1 = datetime.datetime(2007, 12, 19, 22, 25, 0)
        cls.time2 = datetime.datetime(2007, 12, 19, 21, 0, 0)
        time3 = datetime.datetime(2007, 12, 20, 22, 25, 0)
        time4 = datetime.datetime(2007, 12, 20, 21, 0, 0)
        cls.i1 = Item.objects.create(
            name="one",
            created=cls.time1,
            modified=cls.time1,
            creator=cls.a1,
            note=cls.n3,
        )
        cls.i1.tags.set([cls.t1, cls.t2])
        cls.i2 = Item.objects.create(
            name="two", created=cls.time2, creator=cls.a2, note=cls.n2
        )
        cls.i2.tags.set([cls.t1, cls.t3])
        cls.i3 = Item.objects.create(
            name="three", created=time3, creator=cls.a2, note=cls.n3
        )
        cls.i4 = Item.objects.create(
            name="four", created=time4, creator=cls.a4, note=cls.n3
        )
        cls.i4.tags.set([cls.t4])

        cls.r1 = Report.objects.create(name="r1", creator=cls.a1)
        cls.r2 = Report.objects.create(name="r2", creator=cls.a3)
        cls.r3 = Report.objects.create(name="r3")

        # Ordering by 'rank' gives us rank2, rank1, rank3. Ordering by the
        # Meta.ordering will be rank3, rank2, rank1.
        cls.rank1 = Ranking.objects.create(rank=2, author=cls.a2)

        cls.c1 = Cover.objects.create(title="first", item=cls.i4)
        cls.c2 = Cover.objects.create(title="second", item=cls.i2)