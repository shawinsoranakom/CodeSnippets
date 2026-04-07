def test_ticket_11101(self):
        """Fixtures can be rolled back (ticket #11101)."""
        with transaction.atomic():
            management.call_command(
                "loaddata",
                "thingy.json",
                verbosity=0,
            )
            self.assertEqual(Thingy.objects.count(), 1)
            transaction.set_rollback(True)
        self.assertEqual(Thingy.objects.count(), 0)