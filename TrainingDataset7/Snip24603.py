def test_srid(self):
        "Testing GeometryField with a SRID set."
        # Input that doesn't specify the SRID is assumed to be in the SRID
        # of the input field.
        fld = forms.GeometryField(srid=4326)
        geom = fld.clean("POINT(5 23)")
        self.assertEqual(4326, geom.srid)
        # Making the field in a different SRID from that of the geometry, and
        # asserting it transforms.
        fld = forms.GeometryField(srid=32140)
        # Different PROJ versions use different transformations, all are
        # correct as having a 1 meter accuracy.
        tol = 1
        xform_geom = GEOSGeometry(
            "POINT (951640.547328465 4219369.26171664)", srid=32140
        )
        # The cleaned geometry is transformed to 32140 (the widget map_srid is
        # 3857).
        cleaned_geom = fld.clean(
            "SRID=3857;POINT (-10615777.40976205 3473169.895707852)"
        )
        self.assertEqual(cleaned_geom.srid, 32140)
        self.assertTrue(xform_geom.equals_exact(cleaned_geom, tol))