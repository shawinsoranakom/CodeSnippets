def test04_proj(self):
        """PROJ import and export."""
        proj_parts = [
            "+proj=longlat",
            "+ellps=WGS84",
            "+towgs84=0,0,0,0,0,0,0",
            "+datum=WGS84",
            "+no_defs",
        ]
        srs1 = SpatialReference(srlist[0].wkt)
        srs2 = SpatialReference("+proj=longlat +datum=WGS84 +no_defs")
        self.assertTrue(all(part in proj_parts for part in srs1.proj.split()))
        self.assertTrue(all(part in proj_parts for part in srs2.proj.split()))