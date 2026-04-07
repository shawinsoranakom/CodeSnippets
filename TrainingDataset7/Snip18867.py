def runner(main_thread_connection):
                from django.db import connections

                connections["default"] = main_thread_connection
                try:
                    Person.objects.get(first_name="John", last_name="Doe")
                except Exception as e:
                    exceptions.append(e)