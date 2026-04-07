def test_get_choices(self):
        self.assertChoicesEqual(
            self.field.get_choices(include_blank=False, ordering=("a",)),
            [self.foo1, self.foo2],
        )
        self.assertChoicesEqual(
            self.field.get_choices(include_blank=False, ordering=("-a",)),
            [self.foo2, self.foo1],
        )