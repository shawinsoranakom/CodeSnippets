def test_closing_non_shared_connections(self):
        """
        A connection that is not explicitly shareable cannot be closed by
        another thread (#17258).
        """
        # First, without explicitly enabling the connection for sharing.
        exceptions = set()

        def runner1():
            def runner2(other_thread_connection):
                try:
                    other_thread_connection.close()
                except DatabaseError as e:
                    exceptions.add(e)

            t2 = threading.Thread(target=runner2, args=[connections["default"]])
            t2.start()
            t2.join()

        t1 = threading.Thread(target=runner1)
        t1.start()
        t1.join()
        # The exception was raised
        self.assertEqual(len(exceptions), 1)

        # Then, with explicitly enabling the connection for sharing.
        exceptions = set()

        def runner1():
            def runner2(other_thread_connection):
                try:
                    other_thread_connection.close()
                except DatabaseError as e:
                    exceptions.add(e)

            # Enable thread sharing
            connections["default"].inc_thread_sharing()
            try:
                t2 = threading.Thread(target=runner2, args=[connections["default"]])
                t2.start()
                t2.join()
            finally:
                connections["default"].dec_thread_sharing()

        t1 = threading.Thread(target=runner1)
        t1.start()
        t1.join()
        # No exception was raised
        self.assertEqual(len(exceptions), 0)