def test_proxy_model_included(self):
        """
        Regression for #11428 - Proxy models aren't included when you dumpdata
        """
        out = StringIO()
        # Create an instance of the concrete class
        widget = Widget.objects.create(name="grommet")
        management.call_command(
            "dumpdata",
            "fixtures_regress.widget",
            "fixtures_regress.widgetproxy",
            format="json",
            stdout=out,
        )
        self.assertJSONEqual(
            out.getvalue(),
            '[{"pk": %d, "model": "fixtures_regress.widget", '
            '"fields": {"name": "grommet"}}]' % widget.pk,
        )