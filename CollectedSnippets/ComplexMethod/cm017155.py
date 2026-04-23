def test_time_field(self):
        # Getting the database identifier used by OGR, if None returned
        # GDAL does not have the support compiled in.
        ogr_db = get_ogr_db_string()
        if not ogr_db:
            self.skipTest("Unable to setup an OGR connection to your database")

        try:
            # Writing shapefiles via GDAL currently does not support writing
            # OGRTime fields, so we need to actually use a database
            model_def = ogrinspect(
                ogr_db,
                "Measurement",
                layer_key=AllOGRFields._meta.db_table,
                decimal=["f_decimal"],
            )
        except GDALException:
            self.skipTest("Unable to setup an OGR connection to your database")

        self.assertTrue(
            model_def.startswith(
                "# This is an auto-generated Django model module created by "
                "ogrinspect.\n"
                "from django.contrib.gis.db import models\n"
                "\n"
                "\n"
                "class Measurement(models.Model):\n"
            )
        )

        # The ordering of model fields might vary depending on several factors
        # (version of GDAL, etc.).
        if connection.vendor == "sqlite" and GDAL_VERSION < (3, 4):
            # SpatiaLite introspection is somewhat lacking on GDAL < 3.4
            # (#29461).
            self.assertIn("    f_decimal = models.CharField(max_length=0)", model_def)
        else:
            self.assertIn(
                "    f_decimal = models.DecimalField(max_digits=0, decimal_places=0)",
                model_def,
            )
        self.assertIn("    f_int = models.IntegerField()", model_def)
        if not connection.ops.mariadb:
            # Probably a bug between GDAL and MariaDB on time fields.
            self.assertIn("    f_datetime = models.DateTimeField()", model_def)
            self.assertIn("    f_time = models.TimeField()", model_def)
        if connection.vendor == "sqlite" and GDAL_VERSION < (3, 4):
            self.assertIn("    f_float = models.CharField(max_length=0)", model_def)
        else:
            self.assertIn("    f_float = models.FloatField()", model_def)
        max_length = 0 if connection.vendor == "sqlite" else 10
        self.assertIn(
            "    f_char = models.CharField(max_length=%s)" % max_length, model_def
        )
        self.assertIn("    f_date = models.DateField()", model_def)

        # Some backends may have srid=-1
        self.assertIsNotNone(
            re.search(r"    geom = models.PolygonField\(([^\)])*\)", model_def)
        )