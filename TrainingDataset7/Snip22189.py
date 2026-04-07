def test_loading_stdin(self):
        """Loading fixtures from stdin with json and xml."""
        tests_dir = os.path.dirname(__file__)
        fixture_json = os.path.join(tests_dir, "fixtures", "fixture1.json")
        fixture_xml = os.path.join(tests_dir, "fixtures", "fixture3.xml")

        with mock.patch(
            "django.core.management.commands.loaddata.sys.stdin", open(fixture_json)
        ):
            management.call_command("loaddata", "--format=json", "-", verbosity=0)
            self.assertSequenceEqual(
                Article.objects.values_list("headline", flat=True),
                ["Time to reform copyright", "Poker has no place on ESPN"],
            )

        with mock.patch(
            "django.core.management.commands.loaddata.sys.stdin", open(fixture_xml)
        ):
            management.call_command("loaddata", "--format=xml", "-", verbosity=0)
            self.assertSequenceEqual(
                Article.objects.values_list("headline", flat=True),
                [
                    "XML identified as leading cause of cancer",
                    "Time to reform copyright",
                    "Poker on TV is great!",
                ],
            )