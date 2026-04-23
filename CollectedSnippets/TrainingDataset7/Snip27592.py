def test_composite_pk_state(self):
        new_apps = Apps(["migrations"])

        class Foo(models.Model):
            pk = models.CompositePrimaryKey("account_id", "id")
            account_id = models.SmallIntegerField()
            id = models.SmallIntegerField()

            class Meta:
                app_label = "migrations"
                apps = new_apps

        project_state = ProjectState.from_apps(new_apps)
        model_state = project_state.models["migrations", "foo"]
        self.assertEqual(len(model_state.options), 2)
        self.assertEqual(model_state.options["constraints"], [])
        self.assertEqual(model_state.options["indexes"], [])
        self.assertEqual(len(model_state.fields), 3)
        self.assertIn("pk", model_state.fields)
        self.assertIn("account_id", model_state.fields)
        self.assertIn("id", model_state.fields)