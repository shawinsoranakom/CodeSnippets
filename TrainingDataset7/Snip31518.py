def tearDown(self):
        try:
            self.end_blocking_transaction()
        except (DatabaseError, AttributeError):
            pass
        self.new_connection.close()