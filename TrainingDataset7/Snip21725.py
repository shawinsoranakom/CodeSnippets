def test_dates_query(self):
        """
        When calling the dates() method on a queryset with extra selection
        columns, we can (and should) ignore those columns. They don't change
        the result and cause incorrect SQL to be produced otherwise.
        """
        RevisionableModel.objects.create(
            title="First Revision", when=datetime.datetime(2008, 9, 28, 10, 30, 0)
        )

        self.assertSequenceEqual(
            RevisionableModel.objects.extra(select={"the_answer": "id"}).datetimes(
                "when", "month"
            ),
            [datetime.datetime(2008, 9, 1, 0, 0)],
        )