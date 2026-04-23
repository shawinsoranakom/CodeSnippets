def test_multiple_autofields(self):
        msg = (
            "Model invalid_models_tests.MultipleAutoFields can't have more "
            "than one auto-generated field."
        )
        with self.assertRaisesMessage(ValueError, msg):

            class MultipleAutoFields(models.Model):
                auto1 = models.AutoField(primary_key=True)
                auto2 = models.AutoField(primary_key=True)