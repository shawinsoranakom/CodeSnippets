def test_database_writes(self):
        """
        Data written to the database by a view can be read.
        """
        with self.urlopen("/create_model_instance/"):
            pass
        self.assertQuerySetEqual(
            Person.objects.order_by("pk"),
            ["jane", "robert", "emily"],
            lambda b: b.name,
        )