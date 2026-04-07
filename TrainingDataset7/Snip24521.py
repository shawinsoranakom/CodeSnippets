def test_test_fid_range_step(self):
        "Tests the `fid_range` keyword and the `step` keyword of .save()."

        # Function for clearing out all the counties before testing.
        def clear_counties():
            County.objects.all().delete()

        State.objects.bulk_create(
            [State(name="Colorado"), State(name="Hawaii"), State(name="Texas")]
        )

        # Initializing the LayerMapping object to use in these tests.
        lm = LayerMapping(County, co_shp, co_mapping, transform=False, unique="name")

        # Bad feature id ranges should raise a type error.
        bad_ranges = (5.0, "foo", co_shp)
        for bad in bad_ranges:
            with self.assertRaises(TypeError):
                lm.save(fid_range=bad)

        # Step keyword should not be allowed w/`fid_range`.
        fr = (3, 5)  # layer[3:5]
        with self.assertRaises(LayerMapError):
            lm.save(fid_range=fr, step=10)
        lm.save(fid_range=fr)

        # Features IDs 3 & 4 are for Galveston County, Texas -- only
        # one model is returned because the `unique` keyword was set.
        qs = County.objects.all()
        self.assertEqual(1, qs.count())
        self.assertEqual("Galveston", qs[0].name)

        # Features IDs 5 and beyond for Honolulu County, Hawaii, and
        # FID 0 is for Pueblo County, Colorado.
        clear_counties()
        lm.save(fid_range=slice(5, None), silent=True, strict=True)  # layer[5:]
        lm.save(fid_range=slice(None, 1), silent=True, strict=True)  # layer[:1]

        # Only Pueblo & Honolulu counties should be present because of
        # the `unique` keyword. Have to set `order_by` on this QuerySet
        # or else MySQL will return a different ordering than the other dbs.
        qs = County.objects.order_by("name")
        self.assertEqual(2, qs.count())
        hi, co = tuple(qs)
        hi_idx, co_idx = tuple(map(NAMES.index, ("Honolulu", "Pueblo")))
        self.assertEqual("Pueblo", co.name)
        self.assertEqual(NUMS[co_idx], len(co.mpoly))
        self.assertEqual("Honolulu", hi.name)
        self.assertEqual(NUMS[hi_idx], len(hi.mpoly))

        # Testing the `step` keyword -- should get the same counties
        # regardless of we use a step that divides equally, that is odd,
        # or that is larger than the dataset.
        for st in (4, 7, 1000):
            clear_counties()
            lm.save(step=st, strict=True)
            self.county_helper(county_feat=False)