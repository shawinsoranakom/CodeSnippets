def test_collect(self):
        """
        Testing the `Collect` aggregate.
        """
        # Reference query:
        # SELECT AsText(ST_Collect("relatedapp_location"."point"))
        # FROM "relatedapp_city"
        # LEFT OUTER JOIN
        #   "relatedapp_location" ON (
        #       "relatedapp_city"."location_id" = "relatedapp_location"."id"
        #   )
        # WHERE "relatedapp_city"."state" = 'TX';
        ref_geom = GEOSGeometry(
            "MULTIPOINT(-97.516111 33.058333,-96.801611 32.782057,"
            "-95.363151 29.763374,-96.801611 32.782057)"
        )

        coll = City.objects.filter(state="TX").aggregate(Collect("location__point"))[
            "location__point__collect"
        ]
        # Even though Dallas and Ft. Worth share same point, Collect doesn't
        # consolidate -- that's why 4 points in MultiPoint.
        self.assertEqual(4, len(coll))
        self.assertTrue(ref_geom.equals(coll))