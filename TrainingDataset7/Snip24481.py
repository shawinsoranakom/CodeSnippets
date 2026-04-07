def assertGeometryColumnsCount(self, expected_count):
        self.assertEqual(
            GeometryColumns.objects.filter(
                **{
                    "%s__iexact" % GeometryColumns.table_name_col(): "gis_neighborhood",
                }
            ).count(),
            expected_count,
        )