def test_run_python(self):
        """
        Tests the RunPython operation
        """

        project_state = self.set_up_test_model("test_runpython", mti_model=True)

        # Create the operation
        def inner_method(models, schema_editor):
            Pony = models.get_model("test_runpython", "Pony")
            Pony.objects.create(pink=1, weight=3.55)
            Pony.objects.create(weight=5)

        def inner_method_reverse(models, schema_editor):
            Pony = models.get_model("test_runpython", "Pony")
            Pony.objects.filter(pink=1, weight=3.55).delete()
            Pony.objects.filter(weight=5).delete()

        operation = migrations.RunPython(
            inner_method, reverse_code=inner_method_reverse
        )
        self.assertEqual(operation.describe(), "Raw Python operation")
        self.assertEqual(operation.formatted_description(), "p Raw Python operation")
        # Test the state alteration does nothing
        new_state = project_state.clone()
        operation.state_forwards("test_runpython", new_state)
        self.assertEqual(new_state, project_state)
        # Test the database alteration
        self.assertEqual(
            project_state.apps.get_model("test_runpython", "Pony").objects.count(), 0
        )
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_runpython", editor, project_state, new_state
            )
        self.assertEqual(
            project_state.apps.get_model("test_runpython", "Pony").objects.count(), 2
        )
        # Now test reversal
        self.assertTrue(operation.reversible)
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_runpython", editor, project_state, new_state
            )
        self.assertEqual(
            project_state.apps.get_model("test_runpython", "Pony").objects.count(), 0
        )
        # Now test we can't use a string
        with self.assertRaisesMessage(
            ValueError, "RunPython must be supplied with a callable"
        ):
            migrations.RunPython("print 'ahahaha'")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RunPython")
        self.assertEqual(definition[1], [])
        self.assertEqual(sorted(definition[2]), ["code", "reverse_code"])

        # Also test reversal fails, with an operation identical to above but
        # without reverse_code set.
        no_reverse_operation = migrations.RunPython(inner_method)
        self.assertFalse(no_reverse_operation.reversible)
        with connection.schema_editor() as editor:
            no_reverse_operation.database_forwards(
                "test_runpython", editor, project_state, new_state
            )
            with self.assertRaises(NotImplementedError):
                no_reverse_operation.database_backwards(
                    "test_runpython", editor, new_state, project_state
                )
        self.assertEqual(
            project_state.apps.get_model("test_runpython", "Pony").objects.count(), 2
        )

        def create_ponies(models, schema_editor):
            Pony = models.get_model("test_runpython", "Pony")
            pony1 = Pony.objects.create(pink=1, weight=3.55)
            self.assertIsNot(pony1.pk, None)
            pony2 = Pony.objects.create(weight=5)
            self.assertIsNot(pony2.pk, None)
            self.assertNotEqual(pony1.pk, pony2.pk)

        operation = migrations.RunPython(create_ponies)
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_runpython", editor, project_state, new_state
            )
        self.assertEqual(
            project_state.apps.get_model("test_runpython", "Pony").objects.count(), 4
        )
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RunPython")
        self.assertEqual(definition[1], [])
        self.assertEqual(sorted(definition[2]), ["code"])

        def create_shetlandponies(models, schema_editor):
            ShetlandPony = models.get_model("test_runpython", "ShetlandPony")
            pony1 = ShetlandPony.objects.create(weight=4.0)
            self.assertIsNot(pony1.pk, None)
            pony2 = ShetlandPony.objects.create(weight=5.0)
            self.assertIsNot(pony2.pk, None)
            self.assertNotEqual(pony1.pk, pony2.pk)

        operation = migrations.RunPython(create_shetlandponies)
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_runpython", editor, project_state, new_state
            )
        self.assertEqual(
            project_state.apps.get_model("test_runpython", "Pony").objects.count(), 6
        )
        self.assertEqual(
            project_state.apps.get_model(
                "test_runpython", "ShetlandPony"
            ).objects.count(),
            2,
        )
        # And elidable reduction
        self.assertIs(False, operation.reduce(operation, []))
        elidable_operation = migrations.RunPython(inner_method, elidable=True)
        self.assertEqual(elidable_operation.reduce(operation, []), [operation])

        # Test elidable deconstruction
        definition = elidable_operation.deconstruct()
        self.assertIs(definition[2]["elidable"], True)