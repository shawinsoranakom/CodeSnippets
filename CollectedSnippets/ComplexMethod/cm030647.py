def test_wait_socket(self, slow=False):
        from multiprocessing.connection import wait
        l = socket.create_server((socket_helper.HOST, 0))
        addr = l.getsockname()
        readers = []
        procs = []
        dic = {}

        for i in range(4):
            p = multiprocessing.Process(target=self._child_test_wait_socket,
                                        args=(addr, slow))
            p.daemon = True
            p.start()
            procs.append(p)
            self.addCleanup(p.join)

        for i in range(4):
            r, _ = l.accept()
            readers.append(r)
            dic[r] = []
        l.close()

        while readers:
            for r in wait(readers):
                msg = r.recv(32)
                if not msg:
                    readers.remove(r)
                    r.close()
                else:
                    dic[r].append(msg)

        expected = ''.join('%s\n' % i for i in range(10)).encode('ascii')
        for v in dic.values():
            self.assertEqual(b''.join(v), expected)