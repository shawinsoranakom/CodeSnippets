def test_errors(self):
        "Testing the Error handlers."
        # string-based
        for err in self.geometries.errors:
            with (
                self.subTest(err=err.wkt),
                self.assertRaisesMessage((GEOSException, ValueError), err.msg),
            ):
                fromstr(err.wkt)

        # Bad WKB
        with self.assertRaisesMessage(
            GEOSException, self.error_checking_geom.format("GEOSWKBReader_read_r")
        ):
            GEOSGeometry(memoryview(b"0"))

        class NotAGeometry:
            pass

        for geom in (NotAGeometry(), None):
            msg = f"Improper geometry input type: {type(geom)}"
            with (
                self.subTest(geom=geom),
                self.assertRaisesMessage(TypeError, msg),
            ):
                GEOSGeometry(geom)