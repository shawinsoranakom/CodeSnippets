def setUpTestData(cls):
        cls.n1 = Note.objects.create(note="n1", misc="foo", id=1)
        cls.e1 = ExtraInfo.objects.create(info="e1", note=cls.n1)