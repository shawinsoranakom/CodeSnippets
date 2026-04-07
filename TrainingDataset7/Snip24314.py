def test_m_support_error(self):
        geom = GEOSGeometry("POINT M (1 2 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        msg = "GEOSCoordSeq with an M dimension requires GEOS 3.14+."

        # mock geos_version_tuple to be 3.13.13
        with patch(
            "django.contrib.gis.geos.coordseq.geos_version_tuple",
            return_value=(3, 13, 13),
        ):
            with self.assertRaisesMessage(NotImplementedError, msg):
                coord_seq.hasm