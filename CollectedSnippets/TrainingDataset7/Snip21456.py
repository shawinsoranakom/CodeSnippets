def test_right_hand_multiplication(self):
        # RH Multiplication of floats and integers
        Number.objects.filter(pk=self.n.pk).update(
            integer=15 * F("integer"), float=42.7 * F("float")
        )

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 630)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(661.850, places=3)
        )