def test_alias_is_required(self):
        class SomeFunc(StatAggregate):
            function = "TEST"

        with self.assertRaisesMessage(TypeError, "Complex aggregates require an alias"):
            StatTestModel.objects.aggregate(SomeFunc(y="int2", x="int1"))