def test_ticket10028(self):
        # Ordering by model related to nullable relations(!) should use outer
        # joins, so that all results are included.
        p1 = Plaything.objects.create(name="p1")
        self.assertSequenceEqual(Plaything.objects.all(), [p1])