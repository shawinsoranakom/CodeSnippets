def setUpTestData(cls):
        super().setUpTestData()
        band = Band.objects.create(name="Linkin Park")
        cls.album = band.album_set.create(
            name="Hybrid Theory", cover_art=r"albums\hybrid_theory.jpg"
        )