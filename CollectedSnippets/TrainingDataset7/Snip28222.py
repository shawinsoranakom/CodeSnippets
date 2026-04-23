def test_overriding_inherited_FIELD_display(self):
        class Base(models.Model):
            foo = models.CharField(max_length=254, choices=[("A", "Base A")])

            class Meta:
                abstract = True

        class Child(Base):
            foo = models.CharField(
                max_length=254, choices=[("A", "Child A"), ("B", "Child B")]
            )

        self.assertEqual(Child(foo="A").get_foo_display(), "Child A")
        self.assertEqual(Child(foo="B").get_foo_display(), "Child B")