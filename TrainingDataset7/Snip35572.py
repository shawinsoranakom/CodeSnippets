def test_alternate_decorator_syntax_commit(self):
        @transaction.atomic()
        def make_reporter():
            return Reporter.objects.create(first_name="Tintin")

        reporter = make_reporter()
        self.assertSequenceEqual(Reporter.objects.all(), [reporter])