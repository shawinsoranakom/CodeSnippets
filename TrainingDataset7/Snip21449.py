def test_lefthand_power(self):
        # LH Power arithmetic operation on floats and integers
        Number.objects.filter(pk=self.n.pk).update(
            integer=F("integer") ** 2, float=F("float") ** 1.5
        )
        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 1764)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(61.02, places=2)
        )