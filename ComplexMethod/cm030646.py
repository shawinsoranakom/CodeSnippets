def test_wait(self, slow=False):
        from multiprocessing.connection import wait
        readers = []
        procs = []
        messages = []

        for i in range(4):
            r, w = multiprocessing.Pipe(duplex=False)
            p = multiprocessing.Process(target=self._child_test_wait, args=(w, slow))
            p.daemon = True
            p.start()
            w.close()
            readers.append(r)
            procs.append(p)
            self.addCleanup(p.join)

        while readers:
            for r in wait(readers):
                try:
                    msg = r.recv()
                except EOFError:
                    readers.remove(r)
                    r.close()
                else:
                    messages.append(msg)

        messages.sort()
        expected = sorted((i, p.pid) for i in range(10) for p in procs)
        self.assertEqual(messages, expected)