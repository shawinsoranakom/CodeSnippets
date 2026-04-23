def test_window(self):
        self.assertCountEqual(
            AggregateTestModel.objects.annotate(
                integers=Window(
                    expression=ArrayAgg("char_field"),
                    partition_by=F("integer_field"),
                )
            ).values("integers", "char_field"),
            [
                {"integers": ["Foo1", "Foo3"], "char_field": "Foo1"},
                {"integers": ["Foo1", "Foo3"], "char_field": "Foo3"},
                {"integers": ["Foo2"], "char_field": "Foo2"},
                {"integers": ["Foo4"], "char_field": "Foo4"},
            ],
        )