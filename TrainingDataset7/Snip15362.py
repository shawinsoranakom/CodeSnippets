def test_descriptions_render_correctly(self):
        """
        The ``description`` field should render correctly for each field type.
        """
        # help text in fields
        self.assertContains(
            self.response, "<td>first name - The person's first name</td>"
        )
        self.assertContains(
            self.response, "<td>last name - The person's last name</td>"
        )

        # method docstrings
        self.assertContains(self.response, "<p>Get the full name of the person</p>")

        link = '<a class="reference external" href="/admindocs/models/%s/">%s</a>'
        markup = "<p>the related %s object</p>"
        company_markup = markup % (link % ("admin_docs.company", "admin_docs.Company"))

        # foreign keys
        self.assertContains(self.response, company_markup)

        # foreign keys with help text
        self.assertContains(self.response, "%s\n - place of work" % company_markup)

        # many to many fields
        self.assertContains(
            self.response,
            "number of related %s objects"
            % (link % ("admin_docs.group", "admin_docs.Group")),
        )
        self.assertContains(
            self.response,
            "all related %s objects"
            % (link % ("admin_docs.group", "admin_docs.Group")),
        )

        # "raw" and "include" directives are disabled
        self.assertContains(
            self.response,
            "<p>&quot;raw&quot; directive disabled.</p>",
        )
        self.assertContains(
            self.response, ".. raw:: html\n    :file: admin_docs/evilfile.txt"
        )
        self.assertContains(
            self.response,
            "<p>&quot;include&quot; directive disabled.</p>",
        )
        self.assertContains(self.response, ".. include:: admin_docs/evilfile.txt")
        out = self.docutils_stderr.getvalue()
        self.assertIn('"raw" directive disabled', out)
        self.assertIn('"include" directive disabled', out)