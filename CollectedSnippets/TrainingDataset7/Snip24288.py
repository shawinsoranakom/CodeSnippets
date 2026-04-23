def test_geoagg_subquery(self):
        tx = Country.objects.get(name="Texas")
        union = GEOSGeometry("MULTIPOINT(-96.801611 32.782057,-95.363151 29.763374)")
        # Use distinct() to force the usage of a subquery for aggregation.
        with CaptureQueriesContext(connection) as ctx:
            self.assertIs(
                union.equals(
                    City.objects.filter(point__within=tx.mpoly)
                    .distinct()
                    .aggregate(
                        Union("point"),
                    )["point__union"],
                ),
                True,
            )
        self.assertIn("subquery", ctx.captured_queries[0]["sql"])