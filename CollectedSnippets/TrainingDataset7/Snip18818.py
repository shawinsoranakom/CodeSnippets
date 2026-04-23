def test_generic_relation(self):
        """
        Sequence names are correct when resetting generic relations (Ref
        #13941)
        """
        # Create an object with a manually specified PK
        Post.objects.create(id=10, name="1st post", text="hello world")

        # Reset the sequences for the database
        commands = connections[DEFAULT_DB_ALIAS].ops.sequence_reset_sql(
            no_style(), [Post]
        )
        with connection.cursor() as cursor:
            for sql in commands:
                cursor.execute(sql)

        # If we create a new object now, it should have a PK greater
        # than the PK we specified manually.
        obj = Post.objects.create(name="New post", text="goodbye world")
        self.assertGreater(obj.pk, 10)