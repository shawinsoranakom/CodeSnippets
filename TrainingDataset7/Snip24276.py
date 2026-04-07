def test_null_geometries(self):
        "Testing NULL geometry support, and the `isnull` lookup type."
        # Creating a state with a NULL boundary.
        State.objects.create(name="Puerto Rico")

        # Querying for both NULL and Non-NULL values.
        nullqs = State.objects.filter(poly__isnull=True)
        validqs = State.objects.filter(poly__isnull=False)

        # Puerto Rico should be NULL (it's a commonwealth unincorporated
        # territory)
        self.assertEqual(1, len(nullqs))
        self.assertEqual("Puerto Rico", nullqs[0].name)
        # GeometryField=None is an alias for __isnull=True.
        self.assertCountEqual(State.objects.filter(poly=None), nullqs)
        self.assertCountEqual(State.objects.exclude(poly=None), validqs)

        # The valid states should be Colorado & Kansas
        self.assertEqual(2, len(validqs))
        state_names = [s.name for s in validqs]
        self.assertIn("Colorado", state_names)
        self.assertIn("Kansas", state_names)

        # Saving another commonwealth w/a NULL geometry.
        nmi = State.objects.create(name="Northern Mariana Islands", poly=None)
        self.assertIsNone(nmi.poly)

        # Assigning a geometry and saving -- then UPDATE back to NULL.
        nmi.poly = "POLYGON((0 0,1 0,1 1,1 0,0 0))"
        nmi.save()
        State.objects.filter(name="Northern Mariana Islands").update(poly=None)
        self.assertIsNone(State.objects.get(name="Northern Mariana Islands").poly)