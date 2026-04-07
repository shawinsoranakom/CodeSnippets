def test_create_swappable_from_abstract(self):
        """
        A swappable model inheriting from a hierarchy:
        concrete -> abstract -> concrete.
        """
        new_apps = Apps(["migrations"])

        class SearchableLocation(models.Model):
            keywords = models.CharField(max_length=256)

            class Meta:
                app_label = "migrations"
                apps = new_apps

        class Station(SearchableLocation):
            name = models.CharField(max_length=128)

            class Meta:
                abstract = True

        class BusStation(Station):
            bus_routes = models.CharField(max_length=128)
            inbound = models.BooleanField(default=False)

            class Meta(Station.Meta):
                app_label = "migrations"
                apps = new_apps
                swappable = "TEST_SWAPPABLE_MODEL"

        station_state = ModelState.from_model(BusStation)
        self.assertEqual(station_state.app_label, "migrations")
        self.assertEqual(station_state.name, "BusStation")
        self.assertEqual(
            list(station_state.fields),
            ["searchablelocation_ptr", "name", "bus_routes", "inbound"],
        )
        self.assertEqual(station_state.fields["name"].max_length, 128)
        self.assertIs(station_state.fields["bus_routes"].null, False)
        self.assertEqual(
            station_state.options,
            {
                "abstract": False,
                "swappable": "TEST_SWAPPABLE_MODEL",
                "indexes": [],
                "constraints": [],
            },
        )
        self.assertEqual(station_state.bases, ("migrations.searchablelocation",))
        self.assertEqual(station_state.managers, [])