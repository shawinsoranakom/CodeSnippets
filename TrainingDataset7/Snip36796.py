def test_primary_key_unique_check_not_performed_when_adding_and_pk_not_specified(
        self,
    ):
        # Regression test for #12560
        with self.assertNumQueries(0):
            mtv = ModelToValidate(number=10, name="Some Name")
            setattr(mtv, "_adding", True)
            mtv.full_clean()