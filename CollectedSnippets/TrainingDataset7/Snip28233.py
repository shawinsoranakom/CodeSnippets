def test_get_choices_reverse_related_field(self):
        self.assertChoicesEqual(
            self.field.remote_field.get_choices(include_blank=False, ordering=("a",)),
            [self.bar1, self.bar2],
        )
        self.assertChoicesEqual(
            self.field.remote_field.get_choices(include_blank=False, ordering=("-a",)),
            [self.bar2, self.bar1],
        )