def test_geohash(self):
        # Reference query:
        # SELECT ST_GeoHash(point) FROM geoapp_city WHERE name='Houston';
        # SELECT ST_GeoHash(point, 5) FROM geoapp_city WHERE name='Houston';
        ref_hash = "9vk1mfq8jx0c8e0386z6"
        h1 = City.objects.annotate(geohash=functions.GeoHash("point")).get(
            name="Houston"
        )
        h2 = City.objects.annotate(geohash=functions.GeoHash("point", precision=5)).get(
            name="Houston"
        )
        self.assertEqual(ref_hash, h1.geohash[: len(ref_hash)])
        self.assertEqual(ref_hash[:5], h2.geohash)