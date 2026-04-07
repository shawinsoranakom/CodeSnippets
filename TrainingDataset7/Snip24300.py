def test05_geography_layermapping(self):
        "Testing LayerMapping support on models with geography fields."
        # There is a similar test in `layermap` that uses the same data set,
        # but the County model here is a bit different.
        from django.contrib.gis.utils import LayerMapping

        # Getting the shapefile and mapping dictionary.
        shp_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "..", "data")
        )
        co_shp = os.path.join(shp_path, "counties", "counties.shp")
        co_mapping = {
            "name": "Name",
            "state": "State",
            "mpoly": "MULTIPOLYGON",
        }
        # Reference county names, number of polygons, and state names.
        names = ["Bexar", "Galveston", "Harris", "Honolulu", "Pueblo"]
        num_polys = [1, 2, 1, 19, 1]  # Number of polygons for each.
        st_names = ["Texas", "Texas", "Texas", "Hawaii", "Colorado"]

        lm = LayerMapping(County, co_shp, co_mapping, source_srs=4269, unique="name")
        lm.save(silent=True, strict=True)

        for c, name, num_poly, state in zip(
            County.objects.order_by("name"), names, num_polys, st_names
        ):
            self.assertEqual(4326, c.mpoly.srid)
            self.assertEqual(num_poly, len(c.mpoly))
            self.assertEqual(name, c.name)
            self.assertEqual(state, c.state)