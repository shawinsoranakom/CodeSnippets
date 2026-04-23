def test_pointing_to_foreign_object_multi_column(self):
        class Reference(models.Model):
            reference_id = models.IntegerField(unique=True)
            code = models.CharField(max_length=1)

        class ReferenceTabMultiple(models.Model):
            reference_id = models.IntegerField()
            code = models.CharField(max_length=1)
            reference = models.ForeignObject(
                Reference,
                from_fields=["reference_id", "code"],
                to_fields=["reference_id", "code"],
                on_delete=models.CASCADE,
            )

            class Meta:
                unique_together = [["reference"]]

        self.assertEqual(
            ReferenceTabMultiple.check(),
            [
                Error(
                    "'unique_together' refers to a ForeignObject 'reference' with "
                    "multiple 'from_fields', which is not supported for that option.",
                    obj=ReferenceTabMultiple,
                    id="models.E049",
                ),
            ],
        )