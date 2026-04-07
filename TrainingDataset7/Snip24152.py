def test_length(self):
        """
        Testing Length() function on 3D fields.
        """
        # ST_Length_Spheroid Z-aware, and thus does not need to use
        # a separate function internally.
        # `SELECT ST_Length_Spheroid(
        #     line, 'SPHEROID["GRS 1980",6378137,298.257222101]')
        #    FROM geo3d_interstate[2d|3d];`
        self._load_interstate_data()
        tol = 3
        ref_length_2d = 4368.1721949481
        ref_length_3d = 4368.62547052088
        inter2d = Interstate2D.objects.annotate(length=Length("line")).get(name="I-45")
        self.assertAlmostEqual(ref_length_2d, inter2d.length.m, tol)
        inter3d = Interstate3D.objects.annotate(length=Length("line")).get(name="I-45")
        self.assertAlmostEqual(ref_length_3d, inter3d.length.m, tol)

        # Making sure `ST_Length3D` is used on for a projected
        # and 3D model rather than `ST_Length`.
        # `SELECT ST_Length(line) FROM geo3d_interstateproj2d;`
        ref_length_2d = 4367.71564892392
        # `SELECT ST_Length3D(line) FROM geo3d_interstateproj3d;`
        ref_length_3d = 4368.16897234101
        inter2d = InterstateProj2D.objects.annotate(length=Length("line")).get(
            name="I-45"
        )
        self.assertAlmostEqual(ref_length_2d, inter2d.length.m, tol)
        inter3d = InterstateProj3D.objects.annotate(length=Length("line")).get(
            name="I-45"
        )
        self.assertAlmostEqual(ref_length_3d, inter3d.length.m, tol)