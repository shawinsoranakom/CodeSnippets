def test_create_model_m2m(self):
        """
        Test the creation of a model with a ManyToMany field and the
        auto-created "through" model.
        """
        project_state = self.set_up_test_model("test_crmomm")
        operation = migrations.CreateModel(
            "Stable",
            [
                ("id", models.AutoField(primary_key=True)),
                ("ponies", models.ManyToManyField("Pony", related_name="stables")),
            ],
        )
        # Test the state alteration
        new_state = project_state.clone()
        operation.state_forwards("test_crmomm", new_state)
        # Test the database alteration
        self.assertTableNotExists("test_crmomm_stable_ponies")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_crmomm", editor, project_state, new_state)
        self.assertTableExists("test_crmomm_stable")
        self.assertTableExists("test_crmomm_stable_ponies")
        self.assertColumnNotExists("test_crmomm_stable", "ponies")
        # Make sure the M2M field actually works
        with atomic():
            Pony = new_state.apps.get_model("test_crmomm", "Pony")
            Stable = new_state.apps.get_model("test_crmomm", "Stable")
            stable = Stable.objects.create()
            p1 = Pony.objects.create(pink=False, weight=4.55)
            p2 = Pony.objects.create(pink=True, weight=5.43)
            stable.ponies.add(p1, p2)
            self.assertEqual(stable.ponies.count(), 2)
            stable.ponies.all().delete()
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_crmomm", editor, new_state, project_state
            )
        self.assertTableNotExists("test_crmomm_stable")
        self.assertTableNotExists("test_crmomm_stable_ponies")