def test_aggregation_default_using_datetime_from_python(self):
        expr = Min(
            "store__original_opening",
            filter=~Q(store__name="Amazon.com"),
            default=datetime.datetime(1970, 1, 1),
        )
        if connection.vendor == "mysql":
            # Workaround for #30224 for MySQL & MariaDB.
            expr.default = Cast(expr.default, DateTimeField())
        queryset = Book.objects.annotate(oldest_store_opening=expr).order_by("isbn")
        self.assertSequenceEqual(
            queryset.values("isbn", "oldest_store_opening"),
            [
                {
                    "isbn": "013235613",
                    "oldest_store_opening": datetime.datetime(1945, 4, 25, 16, 24, 14),
                },
                {
                    "isbn": "013790395",
                    "oldest_store_opening": datetime.datetime(2001, 3, 15, 11, 23, 37),
                },
                {
                    "isbn": "067232959",
                    "oldest_store_opening": datetime.datetime(1970, 1, 1),
                },
                {
                    "isbn": "155860191",
                    "oldest_store_opening": datetime.datetime(1945, 4, 25, 16, 24, 14),
                },
                {
                    "isbn": "159059725",
                    "oldest_store_opening": datetime.datetime(2001, 3, 15, 11, 23, 37),
                },
                {
                    "isbn": "159059996",
                    "oldest_store_opening": datetime.datetime(1945, 4, 25, 16, 24, 14),
                },
            ],
        )