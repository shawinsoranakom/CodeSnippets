def test_geom_type(self):
        "Testing GeometryField's handling of different geometry types."
        # By default, all geometry types are allowed.
        fld = forms.GeometryField()
        for wkt in (
            "POINT(5 23)",
            "MULTIPOLYGON(((0 0, 0 1, 1 1, 1 0, 0 0)))",
            "LINESTRING(0 0, 1 1)",
        ):
            with self.subTest(wkt=wkt):
                # to_python() uses the SRID of OpenLayersWidget if the
                # converted value doesn't have an SRID.
                self.assertEqual(
                    GEOSGeometry(wkt, srid=fld.widget.map_srid), fld.clean(wkt)
                )

        pnt_fld = forms.GeometryField(geom_type="POINT")
        self.assertEqual(
            GEOSGeometry("POINT(5 23)", srid=pnt_fld.widget.map_srid),
            pnt_fld.clean("POINT(5 23)"),
        )
        # a WKT for any other geom_type will be properly transformed by
        # `to_python`
        self.assertEqual(
            GEOSGeometry("LINESTRING(0 0, 1 1)", srid=pnt_fld.widget.map_srid),
            pnt_fld.to_python("LINESTRING(0 0, 1 1)"),
        )
        # but rejected by `clean`
        with self.assertRaises(ValidationError):
            pnt_fld.clean("LINESTRING(0 0, 1 1)")