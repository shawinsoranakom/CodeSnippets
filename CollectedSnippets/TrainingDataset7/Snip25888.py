def test_multivalued_join_reuse(self):
        self.assertEqual(
            Season.objects.get(Exact(F("games__home"), "NY"), games__away="Boston"),
            self.s1,
        )
        self.assertEqual(
            Season.objects.get(Exact(F("games__home"), "NY") & Q(games__away="Boston")),
            self.s1,
        )
        self.assertEqual(
            Season.objects.get(
                Exact(F("games__home"), "NY") & Exact(F("games__away"), "Boston")
            ),
            self.s1,
        )