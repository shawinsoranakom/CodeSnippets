def setUpTestData(cls):
        cls.Model.objects.bulk_create(
            [
                cls.Model(field="Matthew"),
                cls.Model(field="Cat sat on mat."),
                cls.Model(field="Dog sat on rug."),
            ]
        )