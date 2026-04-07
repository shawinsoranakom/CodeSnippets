def test_thread_sharing_count(self):
        self.assertIs(connection.allow_thread_sharing, False)
        connection.inc_thread_sharing()
        self.assertIs(connection.allow_thread_sharing, True)
        connection.inc_thread_sharing()
        self.assertIs(connection.allow_thread_sharing, True)
        connection.dec_thread_sharing()
        self.assertIs(connection.allow_thread_sharing, True)
        connection.dec_thread_sharing()
        self.assertIs(connection.allow_thread_sharing, False)
        msg = "Cannot decrement the thread sharing count below zero."
        with self.assertRaisesMessage(RuntimeError, msg):
            connection.dec_thread_sharing()