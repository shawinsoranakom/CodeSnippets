def start_blocking_transaction(self):
        self.new_connection.set_autocommit(False)
        # Start a blocking transaction. At some point,
        # end_blocking_transaction() should be called.
        self.cursor = self.new_connection.cursor()
        sql = "SELECT * FROM %(db_table)s %(for_update)s;" % {
            "db_table": Person._meta.db_table,
            "for_update": self.new_connection.ops.for_update_sql(),
        }
        self.cursor.execute(sql, ())
        self.cursor.fetchone()