def test_transform_nosrid(self):
        """Testing `transform` method (no SRID or negative SRID)"""
        msg = "Calling transform() with no SRID set is not supported"
        for srid, clone in itertools.product((None, -1), (True, False)):
            g = GEOSGeometry("POINT (-104.609 38.255)", srid=srid)
            with (
                self.subTest(srid=srid, clone=clone),
                self.assertRaisesMessage(GEOSException, msg),
            ):
                g.transform(2774, clone=clone)