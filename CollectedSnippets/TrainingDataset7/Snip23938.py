def test_updates_in_transaction(self):
        """
        Objects are selected and updated in a transaction to avoid race
        conditions. This test forces update_or_create() to hold the lock
        in another thread for a relatively long time so that it can update
        while it holds the lock. The updated field isn't a field in 'defaults',
        so update_or_create() shouldn't have an effect on it.
        """
        lock_status = {"has_grabbed_lock": False}

        def birthday_sleep():
            lock_status["has_grabbed_lock"] = True
            time.sleep(0.5)
            return date(1940, 10, 10)

        def update_birthday_slowly():
            Person.objects.update_or_create(
                first_name="John", defaults={"birthday": birthday_sleep}
            )
            # Avoid leaking connection for Oracle
            connection.close()

        def lock_wait():
            # timeout after ~0.5 seconds
            for i in range(20):
                time.sleep(0.025)
                if lock_status["has_grabbed_lock"]:
                    return True
            return False

        Person.objects.create(
            first_name="John", last_name="Lennon", birthday=date(1940, 10, 9)
        )

        # update_or_create in a separate thread
        t = Thread(target=update_birthday_slowly)
        before_start = datetime.now()
        t.start()

        if not lock_wait():
            self.skipTest("Database took too long to lock the row")

        # Update during lock
        Person.objects.filter(first_name="John").update(last_name="NotLennon")
        after_update = datetime.now()

        # Wait for thread to finish
        t.join()

        # The update remains and it blocked.
        updated_person = Person.objects.get(first_name="John")
        self.assertGreater(after_update - before_start, timedelta(seconds=0.5))
        self.assertEqual(updated_person.last_name, "NotLennon")