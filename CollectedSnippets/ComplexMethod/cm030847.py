def run_server(self, svrcls, hdlrbase, testfunc):
        server = self.make_server(self.pickaddr(svrcls.address_family),
                                  svrcls, hdlrbase)
        # We had the OS pick a port, so pull the real address out of
        # the server.
        addr = server.server_address
        if verbose:
            print("ADDR =", addr)
            print("CLASS =", svrcls)

        t = threading.Thread(
            name='%s serving' % svrcls,
            target=server.serve_forever,
            # Short poll interval to make the test finish quickly.
            # Time between requests is short enough that we won't wake
            # up spuriously too many times.
            kwargs={'poll_interval':0.01})
        t.daemon = True  # In case this function raises.
        t.start()
        if verbose: print("server running")
        for i in range(3):
            if verbose: print("test client", i)
            testfunc(svrcls.address_family, addr)
        if verbose: print("waiting for server")
        server.shutdown()
        t.join()
        server.server_close()
        self.assertEqual(-1, server.socket.fileno())
        if HAVE_FORKING and isinstance(server, socketserver.ForkingMixIn):
            # bpo-31151: Check that ForkingMixIn.server_close() waits until
            # all children completed
            self.assertFalse(server.active_children)
        if verbose: print("done")