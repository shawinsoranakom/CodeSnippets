def test_pickle(self):
        "Testing pickling and unpickling support."

        # Creating a list of test geometries for pickling,
        # and setting the SRID on some of them.
        def get_geoms(lst, srid=None):
            return [GEOSGeometry(tg.wkt, srid) for tg in lst]

        tgeoms = get_geoms(self.geometries.points)
        tgeoms.extend(get_geoms(self.geometries.multilinestrings, 4326))
        tgeoms.extend(get_geoms(self.geometries.polygons, 3084))
        tgeoms.extend(get_geoms(self.geometries.multipolygons, 3857))
        tgeoms.append(Point(srid=4326))
        tgeoms.append(Point())
        for geom in tgeoms:
            s1 = pickle.dumps(geom)
            g1 = pickle.loads(s1)
            with self.subTest(geom=geom):
                self.assertEqual(geom, g1)
                self.assertEqual(geom.srid, g1.srid)