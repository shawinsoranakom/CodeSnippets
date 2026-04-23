def test_multiinheritance_clash(self):
        class Mother(models.Model):
            clash = models.IntegerField()

        class Father(models.Model):
            clash = models.IntegerField()

        class Child(Mother, Father):
            # Here we have two clashed: id (automatic field) and clash, because
            # both parents define these fields.
            pass

        self.assertEqual(
            Child.check(),
            [
                Error(
                    "The field 'id' from parent model "
                    "'invalid_models_tests.mother' clashes with the field 'id' "
                    "from parent model 'invalid_models_tests.father'.",
                    obj=Child,
                    id="models.E005",
                ),
                Error(
                    "The field 'clash' from parent model "
                    "'invalid_models_tests.mother' clashes with the field 'clash' "
                    "from parent model 'invalid_models_tests.father'.",
                    obj=Child,
                    id="models.E005",
                ),
            ],
        )