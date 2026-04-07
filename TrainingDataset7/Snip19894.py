def test_str(self):
        class Model(models.Model):
            field = GenericForeignKey()

        field = Model._meta.get_field("field")

        self.assertEqual(str(field), "contenttypes_tests.Model.field")