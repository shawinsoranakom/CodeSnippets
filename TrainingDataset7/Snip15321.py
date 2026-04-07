def test_parse_docstring(self):
        title, description, metadata = parse_docstring(self.docstring)
        docstring_title = (
            "This __doc__ output is required for testing. I copied this example from\n"
            "`admindocs` documentation. (TITLE)"
        )
        docstring_description = (
            "Display an individual :model:`myapp.MyModel`.\n\n"
            "**Context**\n\n``RequestContext``\n\n``mymodel``\n"
            "    An instance of :model:`myapp.MyModel`.\n\n"
            "**Template:**\n\n:template:`myapp/my_template.html` "
            "(DESCRIPTION)"
        )
        self.assertEqual(title, docstring_title)
        self.assertEqual(description, docstring_description)
        self.assertEqual(metadata, {"some_metadata": "some data"})