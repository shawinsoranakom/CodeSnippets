def test_default_connection_thread_local(self):
        """
        The default connection (i.e. django.db.connection) is different for
        each thread (#17258).
        """
        # Map connections by id because connections with identical aliases
        # have the same hash.
        connections_dict = {}
        with connection.cursor():
            pass
        connections_dict[id(connection)] = connection

        def runner():
            # Passing django.db.connection between threads doesn't work while
            # connections[DEFAULT_DB_ALIAS] does.
            from django.db import connections

            connection = connections[DEFAULT_DB_ALIAS]
            # Allow thread sharing so the connection can be closed by the
            # main thread.
            connection.inc_thread_sharing()
            with connection.cursor():
                pass
            connections_dict[id(connection)] = connection

        try:
            for x in range(2):
                t = threading.Thread(target=runner)
                t.start()
                t.join()
            # Each created connection got different inner connection.
            self.assertEqual(
                len({conn.connection for conn in connections_dict.values()}), 3
            )
        finally:
            # Finish by closing the connections opened by the other threads
            # (the connection opened in the main thread will automatically be
            # closed on teardown).
            for conn in connections_dict.values():
                if conn is not connection and conn.allow_thread_sharing:
                    conn.validate_thread_sharing()
                    conn._close()
                    conn.dec_thread_sharing()