def test_description_output(self):
        title, description, metadata = parse_docstring(self.docstring)
        description_output = parse_rst(description, "model", "model:admindocs")
        description_rendered = (
            '<p>Display an individual <a class="reference external" '
            'href="/admindocs/models/myapp.mymodel/">myapp.MyModel</a>.</p>\n'
            '<p><strong>Context</strong></p>\n<p><tt class="docutils literal">'
            'RequestContext</tt></p>\n<dl class="docutils">\n<dt><tt class="'
            'docutils literal">mymodel</tt></dt>\n<dd>An instance of <a class="'
            'reference external" href="/admindocs/models/myapp.mymodel/">'
            "myapp.MyModel</a>.</dd>\n</dl>\n<p><strong>Template:</strong></p>"
            '\n<p><a class="reference external" href="/admindocs/templates/'
            'myapp/my_template.html/">myapp/my_template.html</a> (DESCRIPTION)'
            "</p>\n"
        )
        self.assertHTMLEqual(description_output, description_rendered)