def test_date_and_time_template_filters(self):
        tpl = Template("{{ dt|date:'Y-m-d' }} at {{ dt|time:'H:i:s' }}")
        ctx = Context({"dt": datetime.datetime(2011, 9, 1, 20, 20, 20, tzinfo=UTC)})
        self.assertEqual(tpl.render(ctx), "2011-09-01 at 23:20:20")
        with timezone.override(ICT):
            self.assertEqual(tpl.render(ctx), "2011-09-02 at 03:20:20")