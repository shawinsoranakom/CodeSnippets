def test_database_constraint_with_condition(self):
        UniqueConstraintConditionProduct.objects.create(name="p1")
        UniqueConstraintConditionProduct.objects.create(name="p2")
        with self.assertRaises(IntegrityError):
            UniqueConstraintConditionProduct.objects.create(name="p1")