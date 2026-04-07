def test_diamond_shaped_multiple_inheritance_is_depth_first(self):
        """
        In contrast to standard Python MRO, resolution of inherited fields is
        strictly depth-first, rather than breadth-first in diamond-shaped
        cases.

        This is because a copy of the parent field descriptor is placed onto
        the model class in ModelBase.__new__(), rather than the attribute
        lookup going via bases. (It only **looks** like inheritance.)

        Here, Child inherits name from Root, rather than ParentB.
        """

        class Root(models.Model):
            name = models.CharField(max_length=255)

            class Meta:
                abstract = True

        class ParentA(Root):
            class Meta:
                abstract = True

        class ParentB(Root):
            name = models.IntegerField()

            class Meta:
                abstract = True

        class Child(ParentA, ParentB):
            pass

        self.assertEqual(Child.check(), [])
        inherited_field = Child._meta.get_field("name")
        self.assertIsInstance(inherited_field, models.CharField)
        self.assertEqual(inherited_field.max_length, 255)