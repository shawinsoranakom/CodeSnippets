def test_filter_unbound_datetime_with_naive_date(self):
        dt = datetime.date(2011, 9, 1)
        msg = "DateTimeField (unbound) received a naive datetime"
        with self.assertWarnsMessage(RuntimeWarning, msg):
            Event.objects.annotate(unbound_datetime=Now()).filter(unbound_datetime=dt)