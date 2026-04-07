def test_lhs_with_index_rhs_without_index(self):
        with CaptureQueriesContext(connection) as queries:
            RasterModel.objects.filter(
                rast__0__contains=json.loads(JSON_RASTER)
            ).exists()
        # It's easier to check the indexes in the generated SQL than to write
        # tests that cover all index combinations.
        self.assertRegex(queries[-1]["sql"], r"WHERE ST_Contains\([^)]*, 1, [^)]*, 1\)")