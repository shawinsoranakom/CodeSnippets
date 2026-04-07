def test_check_composite_foreign_object(self):
        class Parent(models.Model):
            a = models.PositiveIntegerField()
            b = models.PositiveIntegerField()

            class Meta:
                unique_together = (("a", "b"),)

        class Child(models.Model):
            a = models.PositiveIntegerField()
            b = models.PositiveIntegerField()
            value = models.CharField(max_length=255)
            parent = models.ForeignObject(
                Parent,
                on_delete=models.SET_NULL,
                from_fields=("a", "b"),
                to_fields=("a", "b"),
                related_name="children",
            )

        self.assertEqual(Child._meta.get_field("parent").check(from_model=Child), [])