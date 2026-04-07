def test_cleared_default_ordering(self):
        self.assertIs(Tag.objects.all().ordered, True)
        self.assertIs(Tag.objects.order_by().ordered, False)