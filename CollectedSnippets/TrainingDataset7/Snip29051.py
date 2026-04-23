def setUpTestData(cls):
        cls.band = Band.objects.create(
            name="The Doors",
            bio="",
            sign_date=date(1965, 1, 1),
        )