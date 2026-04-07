def test_valid_case(self):
        class Model(models.Model):
            id = models.AutoField(primary_key=True)

        field = Model._meta.get_field("id")
        self.assertEqual(field.check(), [])