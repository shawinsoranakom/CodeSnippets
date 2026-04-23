def test_lefthand_division(self):
        # LH Division of floats and integers
        Number.objects.filter(pk=self.n.pk).update(
            integer=F("integer") / 2, float=F("float") / 42.7
        )

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 21)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(0.363, places=3)
        )