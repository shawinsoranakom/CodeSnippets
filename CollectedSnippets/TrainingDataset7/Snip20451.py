def setUpTestData(cls):
        Author.objects.bulk_create(
            [
                Author(name="Ivan Ivanov", alias="iivanov"),
                Author(name="Bertha Berthy", alias="bberthy"),
            ]
        )