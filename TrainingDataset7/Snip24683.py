def test_retrieve(self):
        """
        Test retrieval of SpatialRefSys model objects.
        """
        for sd in test_srs:
            srs = self.SpatialRefSys.objects.get(srid=sd["srid"])
            self.assertEqual(sd["srid"], srs.srid)

            # Some of the authority names are borked on Oracle, e.g.,
            # SRID=32140. Also, Oracle Spatial seems to add extraneous info to
            # fields, hence the testing with the 'startswith' flag.
            auth_name, oracle_flag = sd["auth_name"]
            # Compare case-insensitively because srs.auth_name is lowercase
            # ("epsg") on Spatialite.
            if not connection.ops.oracle or oracle_flag:
                self.assertIs(srs.auth_name.upper().startswith(auth_name), True)

            self.assertEqual(sd["auth_srid"], srs.auth_srid)

            # No PROJ and different srtext on Oracle.
            if not connection.ops.oracle:
                self.assertTrue(srs.wkt.startswith(sd["srtext"]))
                self.assertRegex(srs.proj4text, sd["proj_re"])