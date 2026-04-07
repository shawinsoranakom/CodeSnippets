def setUpTestData(cls):
        cls.grand_parent = GrandParent.objects.create(
            email="grand_parent@example.com",
            first_name="grand",
            last_name="parent",
        )