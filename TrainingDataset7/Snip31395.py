def test_check_constraint_exact_jsonfield(self):
        class JSONConstraintModel(Model):
            data = JSONField()

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(JSONConstraintModel)
        self.isolated_local_models = [JSONConstraintModel]
        constraint_name = "check_only_stable_version"
        constraint = CheckConstraint(
            condition=Q(data__version="stable"),
            name=constraint_name,
        )
        JSONConstraintModel._meta.constraints = [constraint]
        with connection.schema_editor() as editor:
            editor.add_constraint(JSONConstraintModel, constraint)
        constraints = self.get_constraints(JSONConstraintModel._meta.db_table)
        self.assertIn(constraint_name, constraints)
        with self.assertRaises(IntegrityError), atomic():
            JSONConstraintModel.objects.create(
                data={"release": "5.0.2dev", "version": "dev"}
            )
        JSONConstraintModel.objects.create(
            data={"release": "5.0.3", "version": "stable"}
        )