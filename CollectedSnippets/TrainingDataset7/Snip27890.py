def test_abstract_model_pending_operations(self):
        """
        Foreign key fields declared on abstract models should not add lazy
        relations to resolve relationship declared as string (#24215).
        """
        pending_ops_before = list(apps._pending_operations.items())

        class AbstractForeignKeyModel(models.Model):
            fk = models.ForeignKey("missing.FK", models.CASCADE)

            class Meta:
                abstract = True

        self.assertIs(AbstractForeignKeyModel._meta.apps, apps)
        self.assertEqual(
            pending_ops_before,
            list(apps._pending_operations.items()),
            "Pending lookup added for a foreign key on an abstract model",
        )