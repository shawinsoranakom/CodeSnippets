def test_run_python_atomic(self):
        """
        Tests the RunPython operation correctly handles the "atomic" keyword
        """
        project_state = self.set_up_test_model("test_runpythonatomic", mti_model=True)

        def inner_method(models, schema_editor):
            Pony = models.get_model("test_runpythonatomic", "Pony")
            Pony.objects.create(pink=1, weight=3.55)
            raise ValueError("Adrian hates ponies.")

        # Verify atomicity when applying.
        atomic_migration = Migration("test", "test_runpythonatomic")
        atomic_migration.operations = [
            migrations.RunPython(inner_method, reverse_code=inner_method)
        ]
        non_atomic_migration = Migration("test", "test_runpythonatomic")
        non_atomic_migration.operations = [
            migrations.RunPython(inner_method, reverse_code=inner_method, atomic=False)
        ]
        # If we're a fully-transactional database, both versions should
        # rollback
        if connection.features.can_rollback_ddl:
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
            with self.assertRaises(ValueError):
                with connection.schema_editor() as editor:
                    atomic_migration.apply(project_state, editor)
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
            with self.assertRaises(ValueError):
                with connection.schema_editor() as editor:
                    non_atomic_migration.apply(project_state, editor)
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
        # Otherwise, the non-atomic operation should leave a row there
        else:
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
            with self.assertRaises(ValueError):
                with connection.schema_editor() as editor:
                    atomic_migration.apply(project_state, editor)
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
            with self.assertRaises(ValueError):
                with connection.schema_editor() as editor:
                    non_atomic_migration.apply(project_state, editor)
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                1,
            )
        # Reset object count to zero and verify atomicity when unapplying.
        project_state.apps.get_model(
            "test_runpythonatomic", "Pony"
        ).objects.all().delete()
        # On a fully-transactional database, both versions rollback.
        if connection.features.can_rollback_ddl:
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
            with self.assertRaises(ValueError):
                with connection.schema_editor() as editor:
                    atomic_migration.unapply(project_state, editor)
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
            with self.assertRaises(ValueError):
                with connection.schema_editor() as editor:
                    non_atomic_migration.unapply(project_state, editor)
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
        # Otherwise, the non-atomic operation leaves a row there.
        else:
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
            with self.assertRaises(ValueError):
                with connection.schema_editor() as editor:
                    atomic_migration.unapply(project_state, editor)
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                0,
            )
            with self.assertRaises(ValueError):
                with connection.schema_editor() as editor:
                    non_atomic_migration.unapply(project_state, editor)
            self.assertEqual(
                project_state.apps.get_model(
                    "test_runpythonatomic", "Pony"
                ).objects.count(),
                1,
            )
        # Verify deconstruction.
        definition = non_atomic_migration.operations[0].deconstruct()
        self.assertEqual(definition[0], "RunPython")
        self.assertEqual(definition[1], [])
        self.assertEqual(sorted(definition[2]), ["atomic", "code", "reverse_code"])