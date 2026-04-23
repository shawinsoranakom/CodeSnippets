def test_remove_index_state_forwards(self):
        project_state = self.set_up_test_model("test_rminsf")
        index = models.Index(fields=["pink"], name="test_rminsf_pony_pink_idx")
        migrations.AddIndex("Pony", index).state_forwards("test_rminsf", project_state)
        old_model = project_state.apps.get_model("test_rminsf", "Pony")
        new_state = project_state.clone()

        operation = migrations.RemoveIndex("Pony", "test_rminsf_pony_pink_idx")
        operation.state_forwards("test_rminsf", new_state)
        new_model = new_state.apps.get_model("test_rminsf", "Pony")
        self.assertIsNot(old_model, new_model)