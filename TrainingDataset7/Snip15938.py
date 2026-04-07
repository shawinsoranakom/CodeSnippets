def setUpTestData(cls):
        cls.n = NestedObjects(using=DEFAULT_DB_ALIAS)
        cls.objs = [cls.cascade_model.objects.create(num=i) for i in range(5)]