def clean_savepoints(self):
        """
        Reset the counter used to generate unique savepoint ids in this thread.
        """
        self.savepoint_state = 0