def test_all_gis_lookups_with_rasters(self):
        """
        Evaluate all possible lookups for all input combinations (i.e.
        raster-raster, raster-geom, geom-raster) and for projected and
        unprojected coordinate systems. This test just checks that the lookup
        can be called, but doesn't check if the result makes logical sense.
        """
        from django.contrib.gis.db.backends.postgis.operations import PostGISOperations

        # Create test raster and geom.
        rast = GDALRaster(json.loads(JSON_RASTER))
        stx_pnt = GEOSGeometry("POINT (-95.370401017314293 29.704867409475465)", 4326)
        stx_pnt.transform(3086)

        lookups = [
            (name, lookup)
            for name, lookup in BaseSpatialField.get_lookups().items()
            if issubclass(lookup, GISLookup)
        ]
        self.assertNotEqual(lookups, [], "No lookups found")
        # Loop through all the GIS lookups.
        for name, lookup in lookups:
            # Construct lookup filter strings.
            combo_keys = [
                field + name
                for field in [
                    "rast__",
                    "rast__",
                    "rastprojected__0__",
                    "rast__",
                    "rastprojected__",
                    "geom__",
                    "rast__",
                ]
            ]
            if issubclass(lookup, DistanceLookupBase):
                # Set lookup values for distance lookups.
                combo_values = [
                    (rast, 50, "spheroid"),
                    (rast, 0, 50, "spheroid"),
                    (rast, 0, D(km=1)),
                    (stx_pnt, 0, 500),
                    (stx_pnt, D(km=1000)),
                    (rast, 500),
                    (json.loads(JSON_RASTER), 500),
                ]
            elif name == "relate":
                # Set lookup values for the relate lookup.
                combo_values = [
                    (rast, "T*T***FF*"),
                    (rast, 0, "T*T***FF*"),
                    (rast, 0, "T*T***FF*"),
                    (stx_pnt, 0, "T*T***FF*"),
                    (stx_pnt, "T*T***FF*"),
                    (rast, "T*T***FF*"),
                    (json.loads(JSON_RASTER), "T*T***FF*"),
                ]
            elif name == "isvalid":
                # The isvalid lookup doesn't make sense for rasters.
                continue
            elif PostGISOperations.gis_operators[name].func:
                # Set lookup values for all function based operators.
                combo_values = [
                    rast,
                    (rast, 0),
                    (rast, 0),
                    (stx_pnt, 0),
                    stx_pnt,
                    rast,
                    json.loads(JSON_RASTER),
                ]
            else:
                # Override band lookup for these, as it's not supported.
                combo_keys[2] = "rastprojected__" + name
                # Set lookup values for all other operators.
                combo_values = [
                    rast,
                    None,
                    rast,
                    stx_pnt,
                    stx_pnt,
                    rast,
                    json.loads(JSON_RASTER),
                ]

            # Create query filter combinations.
            self.assertEqual(
                len(combo_keys),
                len(combo_values),
                "Number of lookup names and values should be the same",
            )
            combos = [x for x in zip(combo_keys, combo_values) if x[1]]
            self.assertEqual(
                [(n, x) for n, x in enumerate(combos) if x in combos[:n]],
                [],
                "There are repeated test lookups",
            )
            combos = [{k: v} for k, v in combos]

            for combo in combos:
                # Apply this query filter.
                qs = RasterModel.objects.filter(**combo)

                # Evaluate normal filter qs.
                self.assertIn(qs.count(), [0, 1])

            # Evaluate on conditional Q expressions.
            qs = RasterModel.objects.filter(Q(**combos[0]) & Q(**combos[1]))
            self.assertIn(qs.count(), [0, 1])