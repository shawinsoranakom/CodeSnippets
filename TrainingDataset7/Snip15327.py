def test_parse_rst_view_case_sensitive(self):
        source = ":view:`myapp.views.Index`"
        rendered = (
            '<p><a class="reference external" '
            'href="/admindocs/views/myapp.views.Index/">myapp.views.Index</a></p>'
        )
        self.assertHTMLEqual(parse_rst(source, "view"), rendered)