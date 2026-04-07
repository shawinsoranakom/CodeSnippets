def test_setter(self):
        # Set the place using assignment notation. Because place is the primary
        # key on Restaurant, the save will create a new restaurant
        self.r1.place = self.p2
        self.r1.save()
        self.assertEqual(
            repr(self.p2.restaurant), "<Restaurant: Ace Hardware the restaurant>"
        )
        self.assertEqual(repr(self.r1.place), "<Place: Ace Hardware the place>")
        self.assertEqual(self.p2.pk, self.r1.pk)
        # Set the place back again, using assignment in the reverse direction.
        self.p1.restaurant = self.r1
        self.assertEqual(
            repr(self.p1.restaurant), "<Restaurant: Demon Dogs the restaurant>"
        )
        r = Restaurant.objects.get(pk=self.p1.id)
        self.assertEqual(repr(r.place), "<Place: Demon Dogs the place>")