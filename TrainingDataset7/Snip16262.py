def test_choice_links(self):
        modeladmin = ModelAdmin(Question, site)
        modeladmin.date_hierarchy = "posted"

        posted_dates = (
            datetime.date(2017, 10, 1),
            datetime.date(2017, 10, 1),
            datetime.date(2017, 12, 15),
            datetime.date(2017, 12, 15),
            datetime.date(2017, 12, 31),
            datetime.date(2018, 2, 1),
        )
        Question.objects.bulk_create(
            Question(question="q", posted=posted) for posted in posted_dates
        )

        tests = (
            ({}, [["year=2017"], ["year=2018"]]),
            ({"year": 2016}, []),
            ({"year": 2017}, [["month=10", "year=2017"], ["month=12", "year=2017"]]),
            ({"year": 2017, "month": 9}, []),
            (
                {"year": 2017, "month": 12},
                [
                    ["day=15", "month=12", "year=2017"],
                    ["day=31", "month=12", "year=2017"],
                ],
            ),
        )
        for query, expected_choices in tests:
            with self.subTest(query=query):
                query = {"posted__%s" % q: val for q, val in query.items()}
                request = self.factory.get("/", query)
                request.user = self.superuser
                changelist = modeladmin.get_changelist_instance(request)
                spec = date_hierarchy(changelist)
                choices = [choice["link"] for choice in spec["choices"]]
                expected_choices = [
                    "&".join("posted__%s" % c for c in choice)
                    for choice in expected_choices
                ]
                expected_choices = [
                    ("?" + choice) if choice else "" for choice in expected_choices
                ]
                self.assertEqual(choices, expected_choices)