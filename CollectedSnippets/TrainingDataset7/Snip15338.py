def testview_docstring_links(self):
        summary = (
            '<h2 class="subhead">This is a view for '
            '<a class="reference external" href="/admindocs/models/myapp.company/">'
            "myapp.Company</a></h2>"
        )
        url = reverse(
            "django-admindocs-views-detail", args=["admin_docs.views.CompanyView"]
        )
        response = self.client.get(url)
        self.assertContains(response, summary, html=True)