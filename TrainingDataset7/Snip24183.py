def test_asgeojson(self):
        if not connection.features.has_AsGeoJSON_function:
            with self.assertRaises(NotSupportedError):
                list(Country.objects.annotate(json=functions.AsGeoJSON("mpoly")))
            return

        pueblo_json = '{"type":"Point","coordinates":[-104.609252,38.255001]}'
        houston_json = json.loads(
            '{"type":"Point","crs":{"type":"name","properties":'
            '{"name":"EPSG:4326"}},"coordinates":[-95.363151,29.763374]}'
        )
        victoria_json = json.loads(
            '{"type":"Point",'
            '"bbox":[-123.30519600,48.46261100,-123.30519600,48.46261100],'
            '"coordinates":[-123.305196,48.462611]}'
        )
        chicago_json = json.loads(
            '{"type":"Point","crs":{"type":"name","properties":{"name":"EPSG:4326"}},'
            '"bbox":[-87.65018,41.85039,-87.65018,41.85039],'
            '"coordinates":[-87.65018,41.85039]}'
        )
        if "crs" in connection.features.unsupported_geojson_options:
            del houston_json["crs"]
            del chicago_json["crs"]
        if "bbox" in connection.features.unsupported_geojson_options:
            del chicago_json["bbox"]
            del victoria_json["bbox"]
        if "precision" in connection.features.unsupported_geojson_options:
            chicago_json["coordinates"] = [-87.650175, 41.850385]

        # Precision argument should only be an integer
        with self.assertRaises(TypeError):
            City.objects.annotate(geojson=functions.AsGeoJSON("point", precision="foo"))

        # Reference queries and values.
        # SELECT ST_AsGeoJson("geoapp_city"."point", 8, 0)
        # FROM "geoapp_city" WHERE "geoapp_city"."name" = 'Pueblo';
        self.assertJSONEqual(
            pueblo_json,
            City.objects.annotate(geojson=functions.AsGeoJSON("point"))
            .get(name="Pueblo")
            .geojson,
        )

        # SELECT ST_AsGeoJson("geoapp_city"."point", 8, 2) FROM "geoapp_city"
        # WHERE "geoapp_city"."name" = 'Houston';
        # This time we want to include the CRS by using the `crs` keyword.
        self.assertJSONEqual(
            City.objects.annotate(json=functions.AsGeoJSON("point", crs=True))
            .get(name="Houston")
            .json,
            houston_json,
        )

        # SELECT ST_AsGeoJson("geoapp_city"."point", 8, 1) FROM "geoapp_city"
        # WHERE "geoapp_city"."name" = 'Houston';
        # This time we include the bounding box by using the `bbox` keyword.
        self.assertJSONEqual(
            City.objects.annotate(geojson=functions.AsGeoJSON("point", bbox=True))
            .get(name="Victoria")
            .geojson,
            victoria_json,
        )

        # SELECT ST_AsGeoJson("geoapp_city"."point", 5, 3) FROM "geoapp_city"
        # WHERE "geoapp_city"."name" = 'Chicago';
        # Finally, we set every available keyword.
        # MariaDB doesn't limit the number of decimals in bbox.
        if connection.ops.mariadb:
            chicago_json["bbox"] = [-87.650175, 41.850385, -87.650175, 41.850385]
        try:
            self.assertJSONEqual(
                City.objects.annotate(
                    geojson=functions.AsGeoJSON(
                        "point", bbox=True, crs=True, precision=5
                    )
                )
                .get(name="Chicago")
                .geojson,
                chicago_json,
            )
        except AssertionError:
            # Give a second chance with different coords rounding.
            chicago_json["coordinates"][1] = 41.85038
            self.assertJSONEqual(
                City.objects.annotate(
                    geojson=functions.AsGeoJSON(
                        "point", bbox=True, crs=True, precision=5
                    )
                )
                .get(name="Chicago")
                .geojson,
                chicago_json,
            )