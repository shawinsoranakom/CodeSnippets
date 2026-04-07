def test_single_parent(self):
        class AbstractBase(models.Model):
            name = models.CharField(max_length=30)

            class Meta:
                abstract = True

        class AbstractDescendant(AbstractBase):
            name = models.CharField(max_length=50)

            class Meta:
                abstract = True

        class DerivedChild(AbstractBase):
            name = models.CharField(max_length=50)

        class DerivedGrandChild(AbstractDescendant):
            pass

        self.assertEqual(AbstractDescendant._meta.get_field("name").max_length, 50)
        self.assertEqual(DerivedChild._meta.get_field("name").max_length, 50)
        self.assertEqual(DerivedGrandChild._meta.get_field("name").max_length, 50)