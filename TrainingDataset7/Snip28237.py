def test_get_choices(self):
        self.assertChoicesEqual(
            self.field.get_choices(include_blank=False, limit_choices_to={"a": "a"}),
            [self.foo1],
        )
        self.assertChoicesEqual(
            self.field.get_choices(include_blank=False, limit_choices_to={}),
            [self.foo1, self.foo2],
        )