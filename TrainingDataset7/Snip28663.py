def test_multiple_inheritance_allows_inherited_field(self):
        """
        Single layer multiple inheritance is as expected, deriving the
        inherited field from the first base.
        """

        class ParentA(models.Model):
            name = models.CharField(max_length=255)

            class Meta:
                abstract = True

        class ParentB(models.Model):
            name = models.IntegerField()

            class Meta:
                abstract = True

        class Child(ParentA, ParentB):
            pass

        self.assertEqual(Child.check(), [])
        inherited_field = Child._meta.get_field("name")
        self.assertIsInstance(inherited_field, models.CharField)
        self.assertEqual(inherited_field.max_length, 255)