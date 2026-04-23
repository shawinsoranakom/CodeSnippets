def test_override_field_with_attr(self):
        class AbstractBase(models.Model):
            first_name = models.CharField(max_length=50)
            last_name = models.CharField(max_length=50)
            middle_name = models.CharField(max_length=30)
            full_name = models.CharField(max_length=150)

            class Meta:
                abstract = True

        class Descendant(AbstractBase):
            middle_name = None

            def full_name(self):
                return self.first_name + self.last_name

        msg = "Descendant has no field named %r"
        with self.assertRaisesMessage(FieldDoesNotExist, msg % "middle_name"):
            Descendant._meta.get_field("middle_name")

        with self.assertRaisesMessage(FieldDoesNotExist, msg % "full_name"):
            Descendant._meta.get_field("full_name")