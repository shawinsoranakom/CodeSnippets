def setUpTestData(cls):
        generic = NamedCategory.objects.create(name="Generic")
        t1 = Tag.objects.create(name="t1", category=generic)
        Tag.objects.create(name="t2", parent=t1, category=generic)
        t3 = Tag.objects.create(name="t3", parent=t1)
        Tag.objects.create(name="t4", parent=t3)
        Tag.objects.create(name="t5", parent=t3)