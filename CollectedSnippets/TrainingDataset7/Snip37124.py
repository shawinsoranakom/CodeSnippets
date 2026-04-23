def setUpTestData(cls):
        cls.numbers = [Number.objects.create(num=i) for i in range(10)]