def test_invalid_nulls_distinct_argument(self):
        msg = "UniqueConstraint.nulls_distinct must be a bool."
        with self.assertRaisesMessage(TypeError, msg):
            models.UniqueConstraint(
                name="uniq_opclasses", fields=["field"], nulls_distinct="NULLS DISTINCT"
            )