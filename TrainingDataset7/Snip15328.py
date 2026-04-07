def test_parse_rst_template_case_sensitive(self):
        source = ":template:`Index.html`"
        rendered = (
            '<p><a class="reference external" href="/admindocs/templates/Index.html/">'
            "Index.html</a></p>"
        )
        self.assertHTMLEqual(parse_rst(source, "template"), rendered)