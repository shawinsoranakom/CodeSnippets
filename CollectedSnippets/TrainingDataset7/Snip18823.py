def create_squares(self, args, paramstyle, multiple):
        opts = Square._meta
        tbl = connection.introspection.identifier_converter(opts.db_table)
        f1 = connection.ops.quote_name(opts.get_field("root").column)
        f2 = connection.ops.quote_name(opts.get_field("square").column)
        if paramstyle == "format":
            query = "INSERT INTO %s (%s, %s) VALUES (%%s, %%s)" % (tbl, f1, f2)
        elif paramstyle == "pyformat":
            query = "INSERT INTO %s (%s, %s) VALUES (%%(root)s, %%(square)s)" % (
                tbl,
                f1,
                f2,
            )
        else:
            raise ValueError("unsupported paramstyle in test")
        with connection.cursor() as cursor:
            if multiple:
                cursor.executemany(query, args)
            else:
                cursor.execute(query, args)