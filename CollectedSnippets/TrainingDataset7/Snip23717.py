def test_get_context_data_receives_extra_context(self, mock):
        """
        MultipleObjectMixin.get_context_data() receives the context set by
        BaseYearArchiveView.get_dated_items(). This behavior is implemented in
        BaseDateListView.get().
        """
        BookSigning.objects.create(event_date=datetime.datetime(2008, 4, 2, 12, 0))
        with self.assertRaisesMessage(
            TypeError, "context must be a dict rather than MagicMock."
        ):
            self.client.get("/dates/booksignings/2008/")
        args, kwargs = mock.call_args
        # These are context values from get_dated_items().
        self.assertEqual(kwargs["year"], datetime.date(2008, 1, 1))
        self.assertIsNone(kwargs["previous_year"])
        self.assertIsNone(kwargs["next_year"])