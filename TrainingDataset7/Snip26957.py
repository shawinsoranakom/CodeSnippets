def test_mti_inheritance_model_removal(self):
        Animal = ModelState(
            "app",
            "Animal",
            [
                ("id", models.AutoField(primary_key=True)),
            ],
        )
        Dog = ModelState("app", "Dog", [], bases=("app.Animal",))
        changes = self.get_changes([Animal, Dog], [Animal])
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["DeleteModel"])
        self.assertOperationAttributes(changes, "app", 0, 0, name="Dog")