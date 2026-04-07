def test_implicit_savepoint_rollback(self):
        """
        MySQL implicitly rolls back savepoints when it deadlocks (#22291).
        """
        Reporter.objects.create(id=1)
        Reporter.objects.create(id=2)

        main_thread_ready = threading.Event()

        def other_thread():
            try:
                with transaction.atomic():
                    Reporter.objects.select_for_update().get(id=1)
                    main_thread_ready.wait()
                    # 1) This line locks... (see below for 2)
                    Reporter.objects.exclude(id=1).update(id=2)
            finally:
                # This is the thread-local connection, not the main connection.
                connection.close()

        other_thread = threading.Thread(target=other_thread)
        other_thread.start()

        with self.assertRaisesMessage(OperationalError, "Deadlock found"):
            # Double atomic to enter a transaction and create a savepoint.
            with transaction.atomic():
                with transaction.atomic():
                    Reporter.objects.select_for_update().get(id=2)
                    main_thread_ready.set()
                    # The two threads can't be synchronized with an event here
                    # because the other thread locks. Sleep for a little while.
                    time.sleep(1)
                    # 2) ... and this line deadlocks. (see above for 1)
                    Reporter.objects.exclude(id=2).update(id=1)

        other_thread.join()