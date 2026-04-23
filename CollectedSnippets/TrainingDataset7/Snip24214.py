def test_num_dimensions(self):
        for c in Country.objects.annotate(num_dims=functions.NumDimensions("mpoly")):
            self.assertEqual(2, c.num_dims)

        ThreeDimensionalFeature.objects.create(
            name="London", geom=Point(-0.126418, 51.500832, 0)
        )
        qs = ThreeDimensionalFeature.objects.annotate(
            num_dims=functions.NumDimensions("geom")
        )
        self.assertEqual(qs[0].num_dims, 3)

        qs = ThreeDimensionalFeature.objects.annotate(
            num_dims=F("geom__num_dimensions")
        )
        self.assertEqual(qs[0].num_dims, 3)

        msg = "'NumDimensions' takes exactly 1 argument (2 given)"
        with self.assertRaisesMessage(TypeError, msg):
            Country.objects.annotate(num_dims=functions.NumDimensions("point", "error"))