def setUp(self):
        transaction.set_autocommit(False)
        self.addCleanup(transaction.set_autocommit, True)
        # The tests access the database after exercising 'atomic', initiating
        # a transaction ; a rollback is required before restoring autocommit.
        self.addCleanup(transaction.rollback)