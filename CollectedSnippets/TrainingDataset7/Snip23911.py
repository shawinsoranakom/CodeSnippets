def test_savepoint_rollback(self):
        """
        The database connection is still usable after a DatabaseError in
        get_or_create() (#20463).
        """
        Tag.objects.create(text="foo")
        with self.assertRaises(DatabaseError):
            # pk 123456789 doesn't exist, so the tag object will be created.
            # Saving triggers a unique constraint violation on 'text'.
            Tag.objects.get_or_create(pk=123456789, defaults={"text": "foo"})
        # Tag objects can be created after the error.
        Tag.objects.create(text="bar")