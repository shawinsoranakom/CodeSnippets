def setUpTestData(cls):
        cls.Model.objects.bulk_create(
            [
                cls.Model(field="àéÖ"),
                cls.Model(field="aeO"),
                cls.Model(field="aeo"),
            ]
        )