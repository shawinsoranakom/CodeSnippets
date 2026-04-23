def test_unsupported_nowait_raises_error(self):
        """
        NotSupportedError is raised if a SELECT...FOR UPDATE NOWAIT is run on
        a database backend that supports FOR UPDATE but not NOWAIT.
        """
        with self.assertRaisesMessage(
            NotSupportedError, "NOWAIT is not supported on this database backend."
        ):
            with transaction.atomic():
                Person.objects.select_for_update(nowait=True).get()