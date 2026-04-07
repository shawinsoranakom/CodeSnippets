def test_ticket7371(self):
        self.assertQuerySetEqual(Related.objects.order_by("custom"), [])