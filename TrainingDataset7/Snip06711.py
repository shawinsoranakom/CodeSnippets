def django_test_skips(self):
        skips = super().django_test_skips
        skips.update(
            {
                "SpatiaLite doesn't support distance lookups with Distance objects.": {
                    "gis_tests.geogapp.tests.GeographyTest.test02_distance_lookup",
                },
            }
        )
        return skips