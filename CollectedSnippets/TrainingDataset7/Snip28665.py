def test_target_field_may_be_pushed_down(self):
        """
        Where the Child model needs to inherit a field from a different base
        than that given by depth-first resolution, the target field can be
        **pushed down** by being re-declared.
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
            name = models.IntegerField()

        self.assertEqual(Child.check(), [])
        inherited_field = Child._meta.get_field("name")
        self.assertIsInstance(inherited_field, models.IntegerField)