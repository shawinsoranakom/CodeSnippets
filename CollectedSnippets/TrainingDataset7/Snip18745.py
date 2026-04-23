def test_database_sharing_in_threads(self):
        thread_connections = []

        def create_object():
            Object.objects.create()
            thread_connections.append(connections[DEFAULT_DB_ALIAS].connection)

        main_connection = connections[DEFAULT_DB_ALIAS].connection
        try:
            create_object()
            thread = threading.Thread(target=create_object)
            thread.start()
            thread.join()
            self.assertEqual(Object.objects.count(), 2)
        finally:
            for conn in thread_connections:
                if conn is not main_connection:
                    conn.close()