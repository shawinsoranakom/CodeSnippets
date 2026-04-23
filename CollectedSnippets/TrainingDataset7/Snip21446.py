def test_lefthand_bitwise_right_shift_operator(self):
        Number.objects.update(integer=F("integer").bitrightshift(2))
        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 10)
        self.assertEqual(Number.objects.get(pk=self.n1.pk).integer, -11)