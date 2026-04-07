def test_missing_docutils(self):
        utils.docutils_is_available = False
        try:
            response = self.client.get(reverse("django-admindocs-docroot"))
            self.assertContains(
                response,
                "<h3>The admin documentation system requires Python’s "
                '<a href="https://docutils.sourceforge.io/">docutils</a> '
                "library.</h3>"
                "<p>Please ask your administrators to install "
                '<a href="https://pypi.org/project/docutils/">docutils</a>.</p>',
                html=True,
            )
            self.assertContains(
                response,
                '<div id="site-name"><a href="/admin/">Django administration</a></div>',
            )
        finally:
            utils.docutils_is_available = True