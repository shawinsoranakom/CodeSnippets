def test_ordering_pointing_to_related_model_pk(self):
        class Parent(models.Model):
            pass

        class Child(models.Model):
            parent = models.ForeignKey(Parent, models.CASCADE)

            class Meta:
                ordering = ("parent__pk",)

        self.assertEqual(Child.check(), [])