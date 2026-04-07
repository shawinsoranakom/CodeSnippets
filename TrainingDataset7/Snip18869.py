def runner2(other_thread_connection):
                try:
                    other_thread_connection.close()
                except DatabaseError as e:
                    exceptions.add(e)