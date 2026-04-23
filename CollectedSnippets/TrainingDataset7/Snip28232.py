def test_get_choices_default_ordering(self):
        self.addCleanup(setattr, Foo._meta, "ordering", Foo._meta.ordering)
        Foo._meta.ordering = ("d",)
        self.assertChoicesEqual(
            self.field.get_choices(include_blank=False), [self.foo2, self.foo1]
        )