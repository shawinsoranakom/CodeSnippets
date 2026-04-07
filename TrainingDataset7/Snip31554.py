def run_select_for_update(self, status, **kwargs):
        """
        Utility method that runs a SELECT FOR UPDATE against all
        Person instances. After the select_for_update, it attempts
        to update the name of the only record, save, and commit.

        This function expects to run in a separate thread.
        """
        status.append("started")
        try:
            # We need to enter transaction management again, as this is done on
            # per-thread basis
            with transaction.atomic():
                person = Person.objects.select_for_update(**kwargs).get()
                person.name = "Fred"
                person.save()
        except (DatabaseError, Person.DoesNotExist) as e:
            status.append(e)
        finally:
            # This method is run in a separate thread. It uses its own
            # database connection. Close it without waiting for the GC.
            connection.close()