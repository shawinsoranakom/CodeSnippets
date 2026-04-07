def raw(status):
            try:
                list(
                    Person.objects.raw(
                        "SELECT * FROM %s %s"
                        % (
                            Person._meta.db_table,
                            connection.ops.for_update_sql(nowait=True),
                        )
                    )
                )
            except DatabaseError as e:
                status.append(e)
            finally:
                # This method is run in a separate thread. It uses its own
                # database connection. Close it without waiting for the GC.
                # Connection cannot be closed on Oracle because cursor is still
                # open.
                if connection.vendor != "oracle":
                    connection.close()