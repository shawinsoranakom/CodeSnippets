def test_lefthand_bitwise_left_shift_operator(self):
        Number.objects.update(integer=F("integer").bitleftshift(2))
        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 168)
        self.assertEqual(Number.objects.get(pk=self.n1.pk).integer, -168)