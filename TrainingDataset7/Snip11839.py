def _set_creation_counter(self):
        """
        Set the creation counter value for this instance and increment the
        class-level copy.
        """
        self.creation_counter = BaseManager.creation_counter
        BaseManager.creation_counter += 1