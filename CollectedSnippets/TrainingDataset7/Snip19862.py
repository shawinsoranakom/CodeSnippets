def test_opclasses_and_fields_same_length(self):
        msg = (
            "UniqueConstraint.fields and UniqueConstraint.opclasses must have "
            "the same number of elements."
        )
        with self.assertRaisesMessage(ValueError, msg):
            models.UniqueConstraint(
                name="uniq_opclasses",
                fields=["field"],
                opclasses=["foo", "bar"],
            )