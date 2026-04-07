def test_unsuported_no_key_raises_error(self):
        """
        NotSupportedError is raised if a SELECT...FOR NO KEY UPDATE... is run
        on a database backend that supports FOR UPDATE but not NO KEY.
        """
        msg = "FOR NO KEY UPDATE is not supported on this database backend."
        with self.assertRaisesMessage(NotSupportedError, msg):
            with transaction.atomic():
                Person.objects.select_for_update(no_key=True).get()