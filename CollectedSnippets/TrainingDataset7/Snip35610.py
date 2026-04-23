def test_nested_outer_durable(self):
        with transaction.atomic(durable=True):
            reporter1 = Reporter.objects.create(first_name="Tintin")
            with transaction.atomic():
                reporter2 = Reporter.objects.create(
                    first_name="Archibald",
                    last_name="Haddock",
                )
        self.assertSequenceEqual(Reporter.objects.all(), [reporter2, reporter1])