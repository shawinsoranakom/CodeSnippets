def end_blocking_transaction(self):
        # Roll back the blocking transaction.
        self.cursor.close()
        self.new_connection.rollback()
        self.new_connection.set_autocommit(True)