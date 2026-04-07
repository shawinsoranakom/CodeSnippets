def test_rename_index(self):
        self.assertOptimizesTo(
            [
                migrations.RenameIndex(
                    "Pony", new_name="mid_name", old_fields=("weight", "pink")
                ),
                migrations.RenameIndex(
                    "Pony", new_name="new_name", old_name="mid_name"
                ),
            ],
            [
                migrations.RenameIndex(
                    "Pony", new_name="new_name", old_fields=("weight", "pink")
                ),
            ],
        )
        self.assertOptimizesTo(
            [
                migrations.RenameIndex(
                    "Pony", new_name="mid_name", old_name="old_name"
                ),
                migrations.RenameIndex(
                    "Pony", new_name="new_name", old_name="mid_name"
                ),
            ],
            [migrations.RenameIndex("Pony", new_name="new_name", old_name="old_name")],
        )
        self.assertDoesNotOptimize(
            [
                migrations.RenameIndex(
                    "Pony", new_name="mid_name", old_name="old_name"
                ),
                migrations.RenameIndex(
                    "Pony", new_name="new_name", old_fields=("weight", "pink")
                ),
            ]
        )