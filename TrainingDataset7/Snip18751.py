def create_object():
            Object.objects.create()
            thread_connections.append(connections[DEFAULT_DB_ALIAS].connection)