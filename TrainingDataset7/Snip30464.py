def setUpTestData(cls):
        Number.objects.bulk_create(Number(num=i, other_num=10 - i) for i in range(10))