def test_right_hand_subtraction(self):
        Number.objects.filter(pk=self.n.pk).update(
            integer=15 - F("integer"), float=42.7 - F("float")
        )

        # RH Subtraction of floats and integers
        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, -27)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(27.200, places=3)
        )