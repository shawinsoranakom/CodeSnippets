def ready(self):
        setting_changed.connect(uninstall_if_needed)
        # Connections may already exist before we are called.
        for conn in connections.all(initialized_only=True):
            if conn.vendor == "postgresql":
                conn.introspection.data_types_reverse.update(
                    {
                        3904: "django.contrib.postgres.fields.IntegerRangeField",
                        3906: "django.contrib.postgres.fields.DecimalRangeField",
                        3910: "django.contrib.postgres.fields.DateTimeRangeField",
                        3912: "django.contrib.postgres.fields.DateRangeField",
                        3926: "django.contrib.postgres.fields.BigIntegerRangeField",
                        # PostgreSQL OIDs may vary depending on the
                        # installation, especially for datatypes from
                        # extensions, e.g. "hstore". In such cases, the
                        # type_display attribute (psycopg 3.2+) should be used.
                        "hstore": "django.contrib.postgres.fields.HStoreField",
                    }
                )
                if conn.connection is not None:
                    register_type_handlers(conn)
        connection_created.connect(register_type_handlers)
        CharField.register_lookup(Unaccent)
        TextField.register_lookup(Unaccent)
        CharField.register_lookup(SearchLookup)
        TextField.register_lookup(SearchLookup)
        CharField.register_lookup(TrigramSimilar)
        TextField.register_lookup(TrigramSimilar)
        CharField.register_lookup(TrigramWordSimilar)
        TextField.register_lookup(TrigramWordSimilar)
        CharField.register_lookup(TrigramStrictWordSimilar)
        TextField.register_lookup(TrigramStrictWordSimilar)
        MigrationWriter.register_serializer(RANGE_TYPES, RangeSerializer)
        IndexExpression.register_wrappers(OrderBy, OpClass, Collate)