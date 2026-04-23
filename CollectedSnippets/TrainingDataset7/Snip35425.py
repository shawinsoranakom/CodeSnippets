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