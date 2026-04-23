def test_ticket7107(self):
        # This shouldn't create an infinite loop.
        self.assertSequenceEqual(Valid.objects.all(), [])