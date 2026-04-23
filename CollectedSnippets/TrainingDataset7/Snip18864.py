def do_thread():
            def runner(main_thread_connection):
                from django.db import connections

                connections["default"] = main_thread_connection
                try:
                    Person.objects.get(first_name="John", last_name="Doe")
                except Exception as e:
                    exceptions.append(e)

            t = threading.Thread(target=runner, args=[connections["default"]])
            t.start()
            t.join()