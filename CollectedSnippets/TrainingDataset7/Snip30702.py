def setUpTestData(cls):
        cls.n1 = Note.objects.create(note="n1", misc="foo", id=1)
        e1 = ExtraInfo.objects.create(info="e1", note=cls.n1)
        cls.a2 = Author.objects.create(name="a2", num=2002, extra=e1)