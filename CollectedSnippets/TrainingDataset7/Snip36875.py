def test_technical_404(self):
        response = self.client.get("/technical404/")
        self.assertContains(response, '<header id="summary">', status_code=404)
        self.assertContains(response, '<main id="info">', status_code=404)
        self.assertContains(response, '<footer id="explanation">', status_code=404)
        self.assertContains(
            response,
            '<pre class="exception_value">Testing technical 404.</pre>',
            status_code=404,
            html=True,
        )
        self.assertContains(response, "Raised by:", status_code=404)
        self.assertContains(
            response,
            "<td>view_tests.views.technical404</td>",
            status_code=404,
        )
        self.assertContains(
            response,
            "<p>The current path, <code>technical404/</code>, matched the "
            "last one.</p>",
            status_code=404,
            html=True,
        )