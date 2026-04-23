def test_composite_pk_operations(self):
        app_label = "test_d8d90af6"
        project_state = self.set_up_test_model(app_label)
        operation_0 = migrations.AlterField(
            "Pony", "id", models.IntegerField(primary_key=True)
        )
        operation_1 = migrations.AddField(
            "Pony", "pk", models.CompositePrimaryKey("id", "pink")
        )
        operation_2 = migrations.AlterField("Pony", "id", models.IntegerField())
        operation_3 = migrations.RemoveField("Pony", "pk")
        table_name = f"{app_label}_pony"

        # 1. Add field (pk).
        new_state = project_state.clone()
        new_state = self.apply_operations(
            app_label, new_state, [operation_0, operation_1]
        )
        self.assertColumnNotExists(table_name, "pk")
        Pony = new_state.apps.get_model(app_label, "pony")
        obj_1 = Pony.objects.create(id=1, weight=1)
        msg = (
            f"obj_1={obj_1}, "
            f"obj_1.id={obj_1.id}, "
            f"obj_1.pink={obj_1.pink}, "
            f"obj_1.pk={obj_1.pk}, "
            f"Pony._meta.pk={repr(Pony._meta.pk)}, "
            f"Pony._meta.get_field('id')={repr(Pony._meta.get_field('id'))}"
        )
        self.assertEqual(obj_1.pink, 3, msg)
        self.assertEqual(obj_1.pk, (obj_1.id, obj_1.pink), msg)

        # 2. Alter field (id -> IntegerField()).
        project_state, new_state = new_state, new_state.clone()
        operation_2.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation_2.database_forwards(app_label, editor, project_state, new_state)
        Pony = new_state.apps.get_model(app_label, "pony")
        obj_1 = Pony.objects.get(id=obj_1.id)
        self.assertEqual(obj_1.pink, 3)
        self.assertEqual(obj_1.pk, (obj_1.id, obj_1.pink))
        obj_2 = Pony.objects.create(id=2, weight=2)
        self.assertEqual(obj_2.id, 2)
        self.assertEqual(obj_2.pink, 3)
        self.assertEqual(obj_2.pk, (obj_2.id, obj_2.pink))

        # 3. Remove field (pk).
        project_state, new_state = new_state, new_state.clone()
        operation_3.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation_3.database_forwards(app_label, editor, project_state, new_state)
        Pony = new_state.apps.get_model(app_label, "pony")
        obj_1 = Pony.objects.get(id=obj_1.id)
        self.assertEqual(obj_1.pk, obj_1.id)
        obj_2 = Pony.objects.get(id=obj_2.id)
        self.assertEqual(obj_2.id, 2)
        self.assertEqual(obj_2.pk, obj_2.id)