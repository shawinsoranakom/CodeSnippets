def setUpTestData(cls):
        UniqueNumber.objects.bulk_create(
            [UniqueNumber(number=1), UniqueNumber(number=2)]
        )