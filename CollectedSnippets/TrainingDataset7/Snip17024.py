def test_aggregation_default_using_date_from_database(self):
        now = timezone.now().astimezone(datetime.UTC)
        expr = Min("book__pubdate", default=TruncDate(NowUTC()))
        queryset = Publisher.objects.annotate(earliest_pubdate=expr).order_by("name")
        self.assertSequenceEqual(
            queryset.values("name", "earliest_pubdate"),
            [
                {"name": "Apress", "earliest_pubdate": datetime.date(2007, 12, 6)},
                {"name": "Jonno's House of Books", "earliest_pubdate": now.date()},
                {
                    "name": "Morgan Kaufmann",
                    "earliest_pubdate": datetime.date(1991, 10, 15),
                },
                {
                    "name": "Prentice Hall",
                    "earliest_pubdate": datetime.date(1995, 1, 15),
                },
                {"name": "Sams", "earliest_pubdate": datetime.date(2008, 3, 3)},
            ],
        )