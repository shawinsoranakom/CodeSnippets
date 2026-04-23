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