def setUp(self):
        # Create a second connection to the default database
        self.conn2 = connection.copy()
        self.conn2.set_autocommit(False)
        # Close down the second connection.
        self.addCleanup(self.conn2.close)
        self.addCleanup(self.conn2.rollback)