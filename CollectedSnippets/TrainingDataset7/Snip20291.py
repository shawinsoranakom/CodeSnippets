def test_required_pk(self):
        # The primary key must be specified, so an error is raised if you
        # try to create an object without it.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Employee.objects.create(first_name="Tom", last_name="Smith")