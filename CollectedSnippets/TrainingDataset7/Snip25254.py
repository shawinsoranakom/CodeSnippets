def test_include_views(self):
        """inspectdb --include-views creates models for database views."""
        cursor_execute(
            "CREATE VIEW inspectdb_people_view AS "
            "SELECT id, name FROM inspectdb_people"
        )
        self.addCleanup(cursor_execute, "DROP VIEW inspectdb_people_view")
        out = StringIO()
        view_model = "class InspectdbPeopleView(models.Model):"
        view_managed = "managed = False  # Created from a view."
        call_command(
            "inspectdb",
            table_name_filter=inspectdb_views_only,
            stdout=out,
        )
        no_views_output = out.getvalue()
        self.assertNotIn(view_model, no_views_output)
        self.assertNotIn(view_managed, no_views_output)
        call_command(
            "inspectdb",
            table_name_filter=inspectdb_views_only,
            include_views=True,
            stdout=out,
        )
        with_views_output = out.getvalue()
        self.assertIn(view_model, with_views_output)
        self.assertIn(view_managed, with_views_output)