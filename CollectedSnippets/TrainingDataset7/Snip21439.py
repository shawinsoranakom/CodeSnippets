def test_lefthand_subtraction(self):
        # LH Subtraction of floats and integers
        Number.objects.filter(pk=self.n.pk).update(
            integer=F("integer") - 15, float=F("float") - 42.7
        )

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 27)
        self.assertEqual(
            Number.objects.get(pk=self.n.pk).float, Approximate(-27.200, places=3)
        )