def test_lefthand_addition(self):
        # LH Addition of floats and integers
        Number.objects.filter(pk=self.n.pk).update(
            integer=F("integer") + 15, float=F("float") + 42.7
        )

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 57)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(58.200, places=3)
        )