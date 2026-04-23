def test_add_check_constraint(self):
        Neighborhood = self.current_state.apps.get_model("gis", "Neighborhood")
        poly = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))
        constraint = models.CheckConstraint(
            condition=models.Q(geom=poly),
            name="geom_within_constraint",
        )
        Neighborhood._meta.constraints = [constraint]
        with connection.schema_editor() as editor:
            editor.add_constraint(Neighborhood, constraint)
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor,
                Neighborhood._meta.db_table,
            )
            self.assertIn("geom_within_constraint", constraints)