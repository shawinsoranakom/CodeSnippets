def test_server_side_binding(self):
        """
        The ORM still generates SQL that is not suitable for usage as prepared
        statements but psycopg >= 3 defaults to using server-side bindings for
        server-side cursors which requires some specialized logic when the
        `server_side_binding` setting is disabled (default).
        """

        def perform_query():
            # Generates SQL that is known to be problematic from a server-side
            # binding perspective as the parametrized ORDER BY clause doesn't
            # use the same binding parameter as the SELECT clause.
            qs = (
                Person.objects.order_by(
                    models.functions.Coalesce("first_name", models.Value(""))
                )
                .distinct()
                .iterator()
            )
            self.assertSequenceEqual(list(qs), [self.p0, self.p1])

        with self.override_db_setting(OPTIONS={}):
            perform_query()

        with self.override_db_setting(OPTIONS={"server_side_binding": False}):
            perform_query()

        with self.override_db_setting(OPTIONS={"server_side_binding": True}):
            # This assertion could start failing the moment the ORM generates
            # SQL suitable for usage as prepared statements (#20516) or if
            # psycopg >= 3 adapts psycopg.Connection(cursor_factory) machinery
            # to allow client-side bindings for named cursors. In the first
            # case this whole test could be removed, in the second one it would
            # most likely need to be adapted.
            with self.assertRaises(ProgrammingError):
                perform_query()