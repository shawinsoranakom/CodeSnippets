def test_create_model_with_boolean_expression_in_check_constraint(self):
        app_label = "test_crmobechc"
        rawsql_constraint = models.CheckConstraint(
            condition=models.expressions.RawSQL(
                "price < %s", (1000,), output_field=models.BooleanField()
            ),
            name=f"{app_label}_price_lt_1000_raw",
        )
        wrapper_constraint = models.CheckConstraint(
            condition=models.expressions.ExpressionWrapper(
                models.Q(price__gt=500) | models.Q(price__lt=500),
                output_field=models.BooleanField(),
            ),
            name=f"{app_label}_price_neq_500_wrap",
        )
        operation = migrations.CreateModel(
            "Product",
            [
                ("id", models.AutoField(primary_key=True)),
                ("price", models.IntegerField(null=True)),
            ],
            options={"constraints": [rawsql_constraint, wrapper_constraint]},
        )

        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        # Add table.
        self.assertTableNotExists(app_label)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertTableExists(f"{app_label}_product")
        insert_sql = f"INSERT INTO {app_label}_product (id, price) VALUES (%d, %d)"
        with connection.cursor() as cursor:
            with self.assertRaises(IntegrityError):
                cursor.execute(insert_sql % (1, 1000))
            cursor.execute(insert_sql % (1, 999))
            with self.assertRaises(IntegrityError):
                cursor.execute(insert_sql % (2, 500))
            cursor.execute(insert_sql % (2, 499))