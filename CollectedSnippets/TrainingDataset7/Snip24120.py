def test02_bad_wkt(self):
        "Testing initialization on invalid WKT."
        for bad in bad_srlist:
            try:
                srs = SpatialReference(bad)
                srs.validate()
            except (SRSException, GDALException):
                pass
            else:
                self.fail('Should not have initialized on bad WKT "%s"!')