def test_loaddata(self):
        "Fixtures can load data into models defined in packages"
        # Load fixture 1. Single JSON file, with two objects
        management.call_command("loaddata", "model_package_fixture1.json", verbosity=0)
        self.assertQuerySetEqual(
            Article.objects.all(),
            [
                "Time to reform copyright",
                "Poker has no place on ESPN",
            ],
            lambda a: a.headline,
        )

        # Load fixture 2. JSON file imported by default. Overwrites some
        # existing objects
        management.call_command("loaddata", "model_package_fixture2.json", verbosity=0)
        self.assertQuerySetEqual(
            Article.objects.all(),
            [
                "Django conquers world!",
                "Copyright is fine the way it is",
                "Poker has no place on ESPN",
            ],
            lambda a: a.headline,
        )

        # Load a fixture that doesn't exist
        with self.assertRaisesMessage(
            CommandError, "No fixture named 'unknown' found."
        ):
            management.call_command("loaddata", "unknown.json", verbosity=0)

        self.assertQuerySetEqual(
            Article.objects.all(),
            [
                "Django conquers world!",
                "Copyright is fine the way it is",
                "Poker has no place on ESPN",
            ],
            lambda a: a.headline,
        )