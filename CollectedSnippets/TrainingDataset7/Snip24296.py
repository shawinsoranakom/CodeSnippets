def test01_fixture_load(self):
        "Ensure geography features loaded properly."
        self.assertEqual(8, City.objects.count())