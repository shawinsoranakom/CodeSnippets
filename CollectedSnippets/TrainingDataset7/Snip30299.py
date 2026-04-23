def test_new_fields(self):
        class NoNewFields(Person):
            newfield = models.BooleanField()

            class Meta:
                proxy = True

        errors = NoNewFields.check()
        expected = [
            checks.Error(
                "Proxy model 'NoNewFields' contains model fields.",
                id="models.E017",
            )
        ]
        self.assertEqual(errors, expected)