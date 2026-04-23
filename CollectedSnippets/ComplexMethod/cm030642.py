def test_notify_all(self):
        cond = self.Condition()
        sleeping = self.Semaphore(0)
        woken = self.Semaphore(0)

        # start some threads/processes which will timeout
        workers = []
        for i in range(3):
            p = self.Process(target=self.f,
                             args=(cond, sleeping, woken, TIMEOUT1))
            p.daemon = True
            p.start()
            workers.append(p)

            t = threading.Thread(target=self.f,
                                 args=(cond, sleeping, woken, TIMEOUT1))
            t.daemon = True
            t.start()
            workers.append(t)

        # wait for them all to sleep
        for i in range(6):
            sleeping.acquire()

        # check they have all timed out
        for i in range(6):
            woken.acquire()
        self.assertReturnsIfImplemented(0, get_value, woken)

        # check state is not mucked up
        self.check_invariant(cond)

        # start some more threads/processes
        for i in range(3):
            p = self.Process(target=self.f, args=(cond, sleeping, woken))
            p.daemon = True
            p.start()
            workers.append(p)

            t = threading.Thread(target=self.f, args=(cond, sleeping, woken))
            t.daemon = True
            t.start()
            workers.append(t)

        # wait for them to all sleep
        for i in range(6):
            sleeping.acquire()

        # check no process/thread has woken up
        time.sleep(DELTA)
        self.assertReturnsIfImplemented(0, get_value, woken)

        # wake them all up
        cond.acquire()
        cond.notify_all()
        cond.release()

        # check they have all woken
        for i in range(6):
            woken.acquire()
        self.assertReturnsIfImplemented(0, get_value, woken)

        # check state is not mucked up
        self.check_invariant(cond)

        for w in workers:
            # NOTE: join_process and join_thread are the same
            threading_helper.join_thread(w)