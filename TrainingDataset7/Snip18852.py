def test_connections_thread_local(self):
        """
        The connections are different for each thread (#17258).
        """
        # Map connections by id because connections with identical aliases
        # have the same hash.
        connections_dict = {}
        for conn in connections.all():
            connections_dict[id(conn)] = conn

        def runner():
            from django.db import connections

            for conn in connections.all():
                # Allow thread sharing so the connection can be closed by the
                # main thread.
                conn.inc_thread_sharing()
                connections_dict[id(conn)] = conn

        try:
            num_new_threads = 2
            for x in range(num_new_threads):
                t = threading.Thread(target=runner)
                t.start()
                t.join()
            self.assertEqual(
                len(connections_dict),
                len(connections.all()) * (num_new_threads + 1),
            )
        finally:
            # Finish by closing the connections opened by the other threads
            # (the connection opened in the main thread will automatically be
            # closed on teardown).
            for conn in connections_dict.values():
                if conn is not connection and conn.allow_thread_sharing:
                    conn.close()
                    conn.dec_thread_sharing()