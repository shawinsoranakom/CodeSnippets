def setUpTestData(cls):
        Band.objects.bulk_create(
            [
                Band(name="Aerosmith", bio="", rank=3),
                Band(name="Radiohead", bio="", rank=1),
                Band(name="Van Halen", bio="", rank=2),
            ]
        )