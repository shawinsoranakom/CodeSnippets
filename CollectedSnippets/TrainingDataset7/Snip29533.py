def test_regr_avgx_with_related_obj_and_number_as_argument(self):
        """
        This is more complex test to check if JOIN on field and
        number as argument works as expected.
        """
        values = StatTestModel.objects.aggregate(
            complex_regravgx=RegrAvgX(y=5, x="related_field__integer_field")
        )
        self.assertEqual(values, {"complex_regravgx": 1.0})