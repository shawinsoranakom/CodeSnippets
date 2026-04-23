def test_righthand_power(self):
        # RH Power arithmetic operation on floats and integers
        Number.objects.filter(pk=self.n.pk).update(
            integer=2 ** F("integer"), float=1.5 ** F("float")
        )
        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 4398046511104)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(536.308, places=3)
        )