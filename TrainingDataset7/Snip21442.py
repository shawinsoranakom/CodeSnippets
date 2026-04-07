def test_lefthand_modulo(self):
        # LH Modulo arithmetic on integers
        Number.objects.filter(pk=self.n.pk).update(integer=F("integer") % 20)
        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 2)