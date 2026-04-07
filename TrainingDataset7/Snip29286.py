def test_rel_pk_exact(self):
        r = Restaurant.objects.first()
        r2 = Restaurant.objects.filter(pk__exact=r).first()
        self.assertEqual(r, r2)