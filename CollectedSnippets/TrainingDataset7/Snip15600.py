def setUpTestData(cls):
        cls.band = Band.objects.create(name="Aerosmith", bio="", rank=3)
        Song.objects.bulk_create(
            [
                Song(band=cls.band, name="Pink", duration=235),
                Song(band=cls.band, name="Dude (Looks Like a Lady)", duration=264),
                Song(band=cls.band, name="Jaded", duration=214),
            ]
        )