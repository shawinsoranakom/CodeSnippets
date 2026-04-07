def test_aggregation_default_using_time_from_database(self):
        now = timezone.now().astimezone(datetime.UTC)
        expr = Min(
            "store__friday_night_closing",
            filter=~Q(store__name="Amazon.com"),
            default=TruncHour(NowUTC(), output_field=TimeField()),
        )
        queryset = Book.objects.annotate(oldest_store_opening=expr).order_by("isbn")
        self.assertSequenceEqual(
            queryset.values("isbn", "oldest_store_opening"),
            [
                {"isbn": "013235613", "oldest_store_opening": datetime.time(21, 30)},
                {
                    "isbn": "013790395",
                    "oldest_store_opening": datetime.time(23, 59, 59),
                },
                {"isbn": "067232959", "oldest_store_opening": datetime.time(now.hour)},
                {"isbn": "155860191", "oldest_store_opening": datetime.time(21, 30)},
                {
                    "isbn": "159059725",
                    "oldest_store_opening": datetime.time(23, 59, 59),
                },
                {"isbn": "159059996", "oldest_store_opening": datetime.time(21, 30)},
            ],
        )