def test_integers_passed_as_strings(self):
        # This checks that get_prep_value is deferred properly
        instance = IntegerArrayModel(field=["1"])
        instance.save()
        loaded = IntegerArrayModel.objects.get()
        self.assertEqual(loaded.field, [1])