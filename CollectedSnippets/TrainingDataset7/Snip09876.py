def get_adapters_template(use_tz, timezone):
        # Create an adapters map extending the base one.
        ctx = adapt.AdaptersMap(adapters)
        # Register a no-op dumper to avoid a round trip from psycopg version 3
        # decode to json.dumps() to json.loads(), when using a custom decoder
        # in JSONField.
        ctx.register_loader("jsonb", TextLoader)
        # Don't convert automatically from PostgreSQL network types to Python
        # ipaddress.
        ctx.register_loader("inet", TextLoader)
        ctx.register_loader("cidr", TextLoader)
        ctx.register_dumper(Range, DjangoRangeDumper)
        # Register a timestamptz loader configured on self.timezone.
        # This, however, can be overridden by create_cursor.
        register_tzloader(timezone, ctx)
        return ctx