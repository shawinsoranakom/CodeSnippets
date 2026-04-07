def test_lefthand_multiplication(self):
        # Multiplication of floats and integers
        Number.objects.filter(pk=self.n.pk).update(
            integer=F("integer") * 15, float=F("float") * 42.7
        )

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 630)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(661.850, places=3)
        )