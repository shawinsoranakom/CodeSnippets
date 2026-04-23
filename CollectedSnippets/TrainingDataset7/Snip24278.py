def test_wkt_string_in_lookup(self):
        # Valid WKT strings don't emit error logs.
        with self.assertNoLogs("django.contrib.gis", "ERROR"):
            State.objects.filter(poly__intersects="LINESTRING(0 0, 1 1, 5 5)")