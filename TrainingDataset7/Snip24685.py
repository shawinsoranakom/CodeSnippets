def test_ellipsoid(self):
        """
        Test the ellipsoid property.
        """
        for sd in test_srs:
            # Getting the ellipsoid and precision parameters.
            ellps1 = sd["ellipsoid"]
            prec = sd["eprec"]

            # Getting our spatial reference and its ellipsoid
            srs = self.SpatialRefSys.objects.get(srid=sd["srid"])
            ellps2 = srs.ellipsoid

            for i in range(3):
                self.assertAlmostEqual(ellps1[i], ellps2[i], prec[i])