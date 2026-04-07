def test_model_docstring_built_in_tag_links(self):
        summary = "Links with different link text."
        body = (
            '<p>This is a line with tag <a class="reference external" '
            'href="/admindocs/tags/#built_in-extends">extends</a>\n'
            'This is a line with model <a class="reference external" '
            'href="/admindocs/models/myapp.family/">Family</a>\n'
            'This is a line with view <a class="reference external" '
            'href="/admindocs/views/myapp.views.Index/">Index</a>\n'
            'This is a line with template <a class="reference external" '
            'href="/admindocs/templates/Index.html/">index template</a>\n'
            'This is a line with filter <a class="reference external" '
            'href="/admindocs/filters/#filtername">example filter</a></p>'
        )
        url = reverse("django-admindocs-models-detail", args=["admin_docs", "family"])
        response = self.client.get(url)
        self.assertContains(response, summary, html=True)
        self.assertContains(response, body, html=True)