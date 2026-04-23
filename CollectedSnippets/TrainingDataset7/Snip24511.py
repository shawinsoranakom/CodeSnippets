def test_management_command(self):
        shp_file = os.path.join(TEST_DATA, "cities", "cities.shp")
        out = StringIO()
        call_command("ogrinspect", shp_file, "City", stdout=out)
        output = out.getvalue()
        self.assertIn("class City(models.Model):", output)