def test_right_hand_addition(self):
        # Right hand operators
        Number.objects.filter(pk=self.n.pk).update(
            integer=15 + F("integer"), float=42.7 + F("float")
        )

        # RH Addition of floats and integers
        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 57)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(58.200, places=3)
        )