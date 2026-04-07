def test_date_and_time_template_filters_honor_localtime(self):
        tpl = Template(
            "{% load tz %}{% localtime off %}{{ dt|date:'Y-m-d' }} at "
            "{{ dt|time:'H:i:s' }}{% endlocaltime %}"
        )
        ctx = Context({"dt": datetime.datetime(2011, 9, 1, 20, 20, 20, tzinfo=UTC)})
        self.assertEqual(tpl.render(ctx), "2011-09-01 at 20:20:20")
        with timezone.override(ICT):
            self.assertEqual(tpl.render(ctx), "2011-09-01 at 20:20:20")