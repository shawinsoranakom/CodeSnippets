def test_pointing_to_foreign_object(self):
        class Reference(models.Model):
            reference_id = models.IntegerField(unique=True)

        class ReferenceTab(models.Model):
            reference_id = models.IntegerField()
            reference = models.ForeignObject(
                Reference,
                from_fields=["reference_id"],
                to_fields=["reference_id"],
                on_delete=models.CASCADE,
            )

            class Meta:
                unique_together = [["reference"]]

        self.assertEqual(ReferenceTab.check(), [])