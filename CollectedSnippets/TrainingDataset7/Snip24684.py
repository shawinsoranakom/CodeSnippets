def test_osr(self):
        """
        Test getting OSR objects from SpatialRefSys model objects.
        """
        for sd in test_srs:
            sr = self.SpatialRefSys.objects.get(srid=sd["srid"])
            self.assertTrue(sr.spheroid.startswith(sd["spheroid"]))
            self.assertEqual(sd["geographic"], sr.geographic)
            self.assertEqual(sd["projected"], sr.projected)
            self.assertIs(sr.name.startswith(sd["name"]), True)
            # Testing the SpatialReference object directly.
            if not connection.ops.oracle:
                srs = sr.srs
                self.assertRegex(srs.proj, sd["proj_re"])
                self.assertTrue(srs.wkt.startswith(sd["srtext"]))