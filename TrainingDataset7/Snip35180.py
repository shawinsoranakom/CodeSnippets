def test_fixture_teardown_checks_constraints(self):
        rollback_atomics = self._rollback_atomics
        self._rollback_atomics = lambda connection: None  # noop
        try:
            car = PossessedCar.objects.create(car_id=1, belongs_to_id=1)
            with self.assertRaises(IntegrityError), transaction.atomic():
                self._fixture_teardown()
            car.delete()
        finally:
            self._rollback_atomics = rollback_atomics