def test_primary_key_unique_check_not_performed_when_not_adding(self):
        # Regression test for #12132
        with self.assertNumQueries(0):
            mtv = ModelToValidate(number=10, name="Some Name")
            mtv.full_clean()