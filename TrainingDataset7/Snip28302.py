def test_choice_value_hash(self):
        value_1 = ModelChoiceIteratorValue(self.c1.pk, self.c1)
        value_2 = ModelChoiceIteratorValue(self.c2.pk, self.c2)
        self.assertEqual(
            hash(value_1), hash(ModelChoiceIteratorValue(self.c1.pk, None))
        )
        self.assertNotEqual(hash(value_1), hash(value_2))