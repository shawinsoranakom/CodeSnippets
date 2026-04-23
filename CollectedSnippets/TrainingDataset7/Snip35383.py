def test_allowed_threaded_database_queries(self):
        connections_dict = {}

        def thread_func():
            # Passing django.db.connection between threads doesn't work while
            # connections[DEFAULT_DB_ALIAS] does.
            from django.db import connections

            connection = connections["default"]

            next(Car.objects.iterator(), None)

            # Allow thread sharing so the connection can be closed by the main
            # thread.
            connection.inc_thread_sharing()
            connections_dict[id(connection)] = connection

        try:
            t = threading.Thread(target=thread_func)
            t.start()
            t.join()
        finally:
            # Finish by closing the connections opened by the other threads
            # (the connection opened in the main thread will automatically be
            # closed on teardown).
            for conn in connections_dict.values():
                if conn is not connection and conn.allow_thread_sharing:
                    conn.validate_thread_sharing()
                    conn._close()
                    conn.dec_thread_sharing()