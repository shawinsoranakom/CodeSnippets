def test_primary_key_unique_check_performed_when_adding_and_pk_specified(self):
        # Regression test for #12560
        with self.assertNumQueries(1):
            mtv = ModelToValidate(number=10, name="Some Name", id=123)
            setattr(mtv, "_adding", True)
            mtv.full_clean()