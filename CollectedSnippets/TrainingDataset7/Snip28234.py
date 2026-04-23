def test_get_choices_reverse_related_field_default_ordering(self):
        self.addCleanup(setattr, Bar._meta, "ordering", Bar._meta.ordering)
        Bar._meta.ordering = ("b",)
        self.assertChoicesEqual(
            self.field.remote_field.get_choices(include_blank=False),
            [self.bar2, self.bar1],
        )