def test07_integer_overflow(self):
        "Testing that OFTReal fields, treated as OFTInteger, do not overflow."
        # Using *.dbf from Census 2010 TIGER Shapefile for Texas,
        # which has land area ('ALAND10') stored in a Real field
        # with no precision.
        ds = DataSource(os.path.join(TEST_DATA, "texas.dbf"))
        feat = ds[0][0]
        # Reference value obtained using `ogrinfo`.
        self.assertEqual(676586997978, feat.get("ALAND10"))