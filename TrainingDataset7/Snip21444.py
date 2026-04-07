def test_lefthand_bitwise_and(self):
        # LH Bitwise ands on integers
        Number.objects.filter(pk=self.n.pk).update(integer=F("integer").bitand(56))
        Number.objects.filter(pk=self.n1.pk).update(integer=F("integer").bitand(-56))

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 40)
        self.assertEqual(Number.objects.get(pk=self.n1.pk).integer, -64)