def close(self):
        self.validate_thread_sharing()
        # If database is in memory, closing the connection destroys the
        # database. To prevent accidental data loss, ignore close requests on
        # an in-memory db.
        if not self.is_in_memory_db():
            BaseDatabaseWrapper.close(self)