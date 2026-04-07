def test_model_docstring_renders_correctly(self):
        summary = (
            '<h2 class="subhead">Stores information about a person, related to '
            '<a class="reference external" href="/admindocs/models/myapp.company/">'
            "myapp.Company</a>.</h2>"
        )
        subheading = "<p><strong>Notes</strong></p>"
        body = (
            '<p>Use <tt class="docutils literal">save_changes()</tt> when saving this '
            "object.</p>"
        )
        model_body = (
            '<dl class="docutils"><dt><tt class="'
            'docutils literal">company</tt></dt><dd>Field storing <a class="'
            'reference external" href="/admindocs/models/myapp.company/">'
            "myapp.Company</a> where the person works.</dd></dl>"
        )
        self.assertContains(self.response, "DESCRIPTION")
        self.assertContains(self.response, summary, html=True)
        self.assertContains(self.response, subheading, html=True)
        self.assertContains(self.response, body, html=True)
        self.assertContains(self.response, model_body, html=True)