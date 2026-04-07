def test_dumpdata_loaddata_cycle(self):
        """
        Test a dumpdata/loaddata cycle with geographic data.
        """
        out = StringIO()
        original_data = list(City.objects.order_by("name"))
        call_command("dumpdata", "geoapp.City", stdout=out)
        result = out.getvalue()
        houston = City.objects.get(name="Houston")
        self.assertIn('"point": "%s"' % houston.point.ewkt, result)

        # Reload now dumped data
        with NamedTemporaryFile(mode="w", suffix=".json") as tmp:
            tmp.write(result)
            tmp.seek(0)
            call_command("loaddata", tmp.name, verbosity=0)
        self.assertEqual(original_data, list(City.objects.order_by("name")))