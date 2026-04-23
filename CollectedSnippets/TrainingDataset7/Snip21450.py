def test_lefthand_bitwise_xor(self):
        Number.objects.update(integer=F("integer").bitxor(48))
        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 26)
        self.assertEqual(Number.objects.get(pk=self.n1.pk).integer, -26)