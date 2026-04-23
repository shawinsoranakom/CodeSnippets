def test_circular_dependency_mixed_addcreate(self):
        """
        #23315 - The dependency resolver knows to put all CreateModel
        before AddField and not become unsolvable.
        """
        address = ModelState(
            "a",
            "Address",
            [
                ("id", models.AutoField(primary_key=True)),
                ("country", models.ForeignKey("b.DeliveryCountry", models.CASCADE)),
            ],
        )
        person = ModelState(
            "a",
            "Person",
            [
                ("id", models.AutoField(primary_key=True)),
            ],
        )
        apackage = ModelState(
            "b",
            "APackage",
            [
                ("id", models.AutoField(primary_key=True)),
                ("person", models.ForeignKey("a.Person", models.CASCADE)),
            ],
        )
        country = ModelState(
            "b",
            "DeliveryCountry",
            [
                ("id", models.AutoField(primary_key=True)),
            ],
        )
        changes = self.get_changes([], [address, person, apackage, country])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "a", 2)
        self.assertNumberMigrations(changes, "b", 1)
        self.assertOperationTypes(changes, "a", 0, ["CreateModel", "CreateModel"])
        self.assertOperationTypes(changes, "a", 1, ["AddField"])
        self.assertOperationTypes(changes, "b", 0, ["CreateModel", "CreateModel"])