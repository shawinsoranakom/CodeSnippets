def setUp(self):
        transaction.set_autocommit(False)
        self.addCleanup(transaction.set_autocommit, True)
        self.addCleanup(transaction.rollback)