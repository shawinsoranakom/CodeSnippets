def setUp(self):
        # A point we are testing distances with -- using a WGS84
        # coordinate that'll be implicitly transformed to that to
        # the coordinate system of the field, EPSG:32140 (Texas South Central
        # w/units in meters)
        self.stx_pnt = GEOSGeometry(
            "POINT (-95.370401017314293 29.704867409475465)", 4326
        )
        # Another one for Australia
        self.au_pnt = GEOSGeometry("POINT (150.791 -34.4919)", 4326)