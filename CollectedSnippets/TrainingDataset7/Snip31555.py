def test_block(self):
        """
        A thread running a select_for_update that accesses rows being touched
        by a similar operation on another connection blocks correctly.
        """
        # First, let's start the transaction in our thread.
        self.start_blocking_transaction()

        # Now, try it again using the ORM's select_for_update
        # facility. Do this in a separate thread.
        status = []
        thread = threading.Thread(target=self.run_select_for_update, args=(status,))

        # The thread should immediately block, but we'll sleep
        # for a bit to make sure.
        thread.start()
        sanity_count = 0
        while len(status) != 1 and sanity_count < 10:
            sanity_count += 1
            time.sleep(1)
        if sanity_count >= 10:
            raise ValueError("Thread did not run and block")

        # Check the person hasn't been updated. Since this isn't
        # using FOR UPDATE, it won't block.
        p = Person.objects.get(pk=self.person.pk)
        self.assertEqual("Reinhardt", p.name)

        # When we end our blocking transaction, our thread should
        # be able to continue.
        self.end_blocking_transaction()
        thread.join(5.0)

        # Check the thread has finished. Assuming it has, we should
        # find that it has updated the person's name.
        self.assertFalse(thread.is_alive())

        # We must commit the transaction to ensure that MySQL gets a fresh
        # read, since by default it runs in REPEATABLE READ mode
        transaction.commit()

        p = Person.objects.get(pk=self.person.pk)
        self.assertEqual("Fred", p.name)