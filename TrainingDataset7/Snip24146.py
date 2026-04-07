def test_union(self):
        """
        Testing the Union aggregate of 3D models.
        """
        # PostGIS query that returned the reference EWKT for this test:
        #  `SELECT ST_AsText(ST_Union(point)) FROM geo3d_city3d;`
        self._load_city_data()
        ref_ewkt = (
            "SRID=4326;MULTIPOINT(-123.305196 48.462611 15,-104.609252 38.255001 1433,"
            "-97.521157 34.464642 380,-96.801611 32.782057 147,-95.363151 29.763374 18,"
            "-95.23506 38.971823 251,-87.650175 41.850385 181,174.783117 -41.315268 14)"
        )
        ref_union = GEOSGeometry(ref_ewkt)
        union = City3D.objects.aggregate(Union("point"))["point__union"]
        self.assertTrue(union.hasz)
        # Ordering of points in the resulting geometry may vary between
        # implementations
        self.assertEqual({p.ewkt for p in ref_union}, {p.ewkt for p in union})