def test_choices_validation_supports_named_groups_nested_dicts(self):
        f = models.IntegerField(choices={"group": {10: "A", 20: "B"}, 30: "C"})
        self.assertEqual(10, f.clean(10, None))