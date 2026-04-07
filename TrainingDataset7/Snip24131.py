def test_unicode(self):
        wkt = (
            'PROJCS["DHDN / Soldner 39 Langschoß",'
            'GEOGCS["DHDN",DATUM["Deutsches_Hauptdreiecksnetz",'
            'SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],'
            'AUTHORITY["EPSG","6314"]],'
            'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],'
            'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
            'AUTHORITY["EPSG","4314"]],PROJECTION["Cassini_Soldner"],'
            'PARAMETER["latitude_of_origin",50.66738711],'
            'PARAMETER["central_meridian",6.28935703],'
            'PARAMETER["false_easting",0],PARAMETER["false_northing",0],'
            'UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",NORTH],AXIS["Y",EAST],'
            'AUTHORITY["mj10777.de","187939"]]'
        )
        srs = SpatialReference(wkt)
        srs_list = [srs, srs.clone()]
        srs.import_wkt(wkt)

        for srs in srs_list:
            self.assertEqual(srs.name, "DHDN / Soldner 39 Langschoß")
            self.assertEqual(srs.wkt, wkt)
            self.assertIn("Langschoß", srs.pretty_wkt)
            if GDAL_VERSION < (3, 9):
                self.assertIn("Langschoß", srs.xml)