def test_commit(self):
        with transaction.atomic():
            reporter = Reporter.objects.create(first_name="Tintin")
        self.assertSequenceEqual(Reporter.objects.all(), [reporter])