def test_m2m_field_argument_validation(self):
        """
        ManyToManyField accepts the ``through_fields`` kwarg
        only if an intermediary table is specified.
        """

        class Fan(models.Model):
            pass

        with self.assertRaisesMessage(
            ValueError, "Cannot specify through_fields without a through model"
        ):
            models.ManyToManyField(Fan, through_fields=("f1", "f2"))