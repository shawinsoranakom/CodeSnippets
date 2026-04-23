def test_complex_expressions(self):
        """
        Complex expressions of different connection types are possible.
        """
        n = Number.objects.create(integer=10, float=123.45)
        self.assertEqual(
            Number.objects.filter(pk=n.pk).update(float=F("integer") + F("float") * 2),
            1,
        )

        self.assertEqual(Number.objects.get(pk=n.pk).integer, 10)
        self.assertEqual(
            Number.objects.get(pk=n.pk).float, Approximate(256.900, places=3)
        )