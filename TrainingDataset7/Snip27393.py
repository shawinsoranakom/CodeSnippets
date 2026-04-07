def test_rename_index_arguments(self):
        msg = "RenameIndex.old_name and old_fields are mutually exclusive."
        with self.assertRaisesMessage(ValueError, msg):
            migrations.RenameIndex(
                "Pony",
                new_name="new_idx_name",
                old_name="old_idx_name",
                old_fields=("weight", "pink"),
            )
        msg = "RenameIndex requires one of old_name and old_fields arguments to be set."
        with self.assertRaisesMessage(ValueError, msg):
            migrations.RenameIndex("Pony", new_name="new_idx_name")