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