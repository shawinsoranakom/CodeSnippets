def test_memsize(self):
        ptown = City.objects.annotate(size=functions.MemSize("point")).get(
            name="Pueblo"
        )
        # Exact value depends on database and version.
        self.assertTrue(20 <= ptown.size <= 105)