def setUpTestData(cls):
        cls.r = Category.objects.create(id=None, name="Root category", parent=None)
        cls.c = Category.objects.create(id=None, name="Child category", parent=cls.r)