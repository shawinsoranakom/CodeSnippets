def test_update_one_to_one_pk(self):
        p1 = Place.objects.create()
        p2 = Place.objects.create()
        r1 = Restaurant.objects.create(place=p1)
        r2 = Restaurant.objects.create(place=p2)
        w = Waiter.objects.create(restaurant=r1)

        Waiter.objects.update(restaurant=r2)
        w.refresh_from_db()
        self.assertEqual(w.restaurant, r2)