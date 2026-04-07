def test_right_hand_division(self):
        # RH Division of floats and integers
        Number.objects.filter(pk=self.n.pk).update(
            integer=640 / F("integer"), float=42.7 / F("float")
        )

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 15)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(2.755, places=3)
        )