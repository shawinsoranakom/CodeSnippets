def test_right_hand_modulo(self):
        # RH Modulo arithmetic on integers
        Number.objects.filter(pk=self.n.pk).update(integer=69 % F("integer"))

        self.assertEqual(Number.objects.get(pk=self.n.pk).integer, 27)