def test_boolean_type(self):
        d = Donut(name="Apple Fritter")
        self.assertFalse(d.is_frosted)
        self.assertIsNone(d.has_sprinkles)
        d.has_sprinkles = True
        self.assertTrue(d.has_sprinkles)

        d.save()

        d2 = Donut.objects.get(name="Apple Fritter")
        self.assertFalse(d2.is_frosted)
        self.assertTrue(d2.has_sprinkles)