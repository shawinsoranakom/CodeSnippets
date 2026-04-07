def test_lefthand_bitwise_or(self):
        # LH Bitwise or on integers
        Number.objects.update(integer=F("integer").bitor(48))

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 58)
        self.assertEqual(Number.objects.get(pk=self.n1.pk).integer, -10)