def test_update_fields_not_updated(self):
        obj = Person.objects.create(name="Sara", gender="F")
        Person.objects.filter(pk=obj.pk).delete()
        msg = "Save with update_fields did not affect any rows."
        # Make sure backward compatibility with DatabaseError is preserved.
        exceptions = [DatabaseError, ObjectNotUpdated, Person.NotUpdated]
        for exception in exceptions:
            with (
                self.subTest(exception),
                self.assertRaisesMessage(DatabaseError, msg),
                transaction.atomic(),
            ):
                obj.save(update_fields=["name"])