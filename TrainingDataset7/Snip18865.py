def runner1():
            def runner2(other_thread_connection):
                try:
                    other_thread_connection.close()
                except DatabaseError as e:
                    exceptions.add(e)

            t2 = threading.Thread(target=runner2, args=[connections["default"]])
            t2.start()
            t2.join()