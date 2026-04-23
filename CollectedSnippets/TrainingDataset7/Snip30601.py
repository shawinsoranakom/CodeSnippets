def test_tickets_7087_12242(self):
        # Dates with extra select columns
        self.assertSequenceEqual(
            Item.objects.datetimes("created", "day").extra(select={"a": 1}),
            [
                datetime.datetime(2007, 12, 19, 0, 0),
                datetime.datetime(2007, 12, 20, 0, 0),
            ],
        )
        self.assertSequenceEqual(
            Item.objects.extra(select={"a": 1}).datetimes("created", "day"),
            [
                datetime.datetime(2007, 12, 19, 0, 0),
                datetime.datetime(2007, 12, 20, 0, 0),
            ],
        )

        name = "one"
        self.assertSequenceEqual(
            Item.objects.datetimes("created", "day").extra(
                where=["name=%s"], params=[name]
            ),
            [datetime.datetime(2007, 12, 19, 0, 0)],
        )

        self.assertSequenceEqual(
            Item.objects.extra(where=["name=%s"], params=[name]).datetimes(
                "created", "day"
            ),
            [datetime.datetime(2007, 12, 19, 0, 0)],
        )