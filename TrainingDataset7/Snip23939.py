def test_creation_in_transaction(self):
        """
        Objects are selected and updated in a transaction to avoid race
        conditions. This test checks the behavior of update_or_create() when
        the object doesn't already exist, but another thread creates the
        object before update_or_create() does and then attempts to update the
        object, also before update_or_create(). It forces update_or_create() to
        hold the lock in another thread for a relatively long time so that it
        can update while it holds the lock. The updated field isn't a field in
        'defaults', so update_or_create() shouldn't have an effect on it.
        """
        locked_for_update = Event()
        save_allowed = Event()

        def wait_or_fail(event, message):
            if not event.wait(5):
                raise AssertionError(message)

        def birthday_yield():
            # At this point the row should be locked as create or update
            # defaults are only called once the SELECT FOR UPDATE is issued.
            locked_for_update.set()
            # Yield back the execution to the main thread until it allows
            # save() to proceed.
            save_allowed.clear()
            return date(1940, 10, 10)

        person_save = Person.save

        def wait_for_allowed_save(*args, **kwargs):
            wait_or_fail(save_allowed, "Test took too long to allow save")
            return person_save(*args, **kwargs)

        def update_person():
            try:
                with patch.object(Person, "save", wait_for_allowed_save):
                    Person.objects.update_or_create(
                        first_name="John",
                        defaults={"last_name": "Doe", "birthday": birthday_yield},
                    )
            finally:
                # Avoid leaking connection for Oracle.
                connection.close()

        t = Thread(target=update_person)
        t.start()
        wait_or_fail(locked_for_update, "Database took too long to lock row")
        # Create object *after* initial attempt by update_or_create to get obj
        # but before creation attempt.
        person = Person(
            first_name="John", last_name="Lennon", birthday=date(1940, 10, 9)
        )
        # Don't use person.save() as it's gated by the save_allowed event.
        person_save(person, force_insert=True)
        # Now that the row is created allow the update_or_create() logic to
        # attempt a save(force_insert) that will inevitably fail and wait
        # until it yields back execution after performing a subsequent
        # locked select for update with an intent to save(force_update).
        locked_for_update.clear()
        save_allowed.set()
        wait_or_fail(locked_for_update, "Database took too long to lock row")
        allow_save = Timer(0.5, save_allowed.set)
        before_start = datetime.now()
        allow_save.start()
        # The following update() should block until the update_or_create()
        # initiated save() is allowed to proceed by the `allow_save` timer
        # setting `save_allowed` after 0.5 seconds.
        Person.objects.filter(first_name="John").update(last_name="NotLennon")
        after_update = datetime.now()
        # Wait for thread to finish.
        t.join()
        # Check call to update_or_create() succeeded and the subsequent
        # (blocked) call to update().
        updated_person = Person.objects.get(first_name="John")
        # Confirm update_or_create() performed an update.
        self.assertEqual(updated_person.birthday, date(1940, 10, 10))
        # Confirm update() was the last statement to run.
        self.assertEqual(updated_person.last_name, "NotLennon")
        # Confirm update() blocked at least the duration of the timer.
        self.assertGreater(after_update - before_start, timedelta(seconds=0.5))