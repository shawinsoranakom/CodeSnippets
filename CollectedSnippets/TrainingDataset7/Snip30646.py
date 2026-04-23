def test_ticket7759(self):
        # Count should work with a partially read result set.
        count = Number.objects.count()
        qs = Number.objects.all()

        def run():
            for obj in qs:
                return qs.count() == count

        self.assertTrue(run())