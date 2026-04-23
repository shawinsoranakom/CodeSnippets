def runner():
            from django.db import connections

            for conn in connections.all():
                # Allow thread sharing so the connection can be closed by the
                # main thread.
                conn.inc_thread_sharing()
                connections_dict[id(conn)] = conn