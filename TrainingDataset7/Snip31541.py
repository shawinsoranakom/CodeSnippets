def test_unsupported_skip_locked_raises_error(self):
        """
        NotSupportedError is raised if a SELECT...FOR UPDATE SKIP LOCKED is run
        on a database backend that supports FOR UPDATE but not SKIP LOCKED.
        """
        with self.assertRaisesMessage(
            NotSupportedError, "SKIP LOCKED is not supported on this database backend."
        ):
            with transaction.atomic():
                Person.objects.select_for_update(skip_locked=True).get()