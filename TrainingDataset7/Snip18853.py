def test_pass_connection_between_threads(self):
        """
        A connection can be passed from one thread to the other (#17258).
        """
        Person.objects.create(first_name="John", last_name="Doe")

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

        # Without touching thread sharing, which should be False by default.
        exceptions = []
        do_thread()
        # Forbidden!
        self.assertIsInstance(exceptions[0], DatabaseError)
        connections["default"].close()

        # After calling inc_thread_sharing() on the connection.
        connections["default"].inc_thread_sharing()
        try:
            exceptions = []
            do_thread()
            # All good
            self.assertEqual(exceptions, [])
        finally:
            connections["default"].dec_thread_sharing()