def test08_defer_only(self):
        "Testing defer() and only() on Geographic models."
        qs = Location.objects.all().order_by("pk")
        def_qs = Location.objects.defer("point").order_by("pk")
        for loc, def_loc in zip(qs, def_qs):
            self.assertEqual(loc.point, def_loc.point)