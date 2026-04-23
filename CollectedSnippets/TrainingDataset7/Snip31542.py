def test_unsupported_of_raises_error(self):
        """
        NotSupportedError is raised if a SELECT...FOR UPDATE OF... is run on
        a database backend that supports FOR UPDATE but not OF.
        """
        msg = "FOR UPDATE OF is not supported on this database backend."
        with self.assertRaisesMessage(NotSupportedError, msg):
            with transaction.atomic():
                Person.objects.select_for_update(of=("self",)).get()