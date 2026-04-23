def server(sock):
            incoming = ssl.MemoryBIO()
            outgoing = ssl.MemoryBIO()
            sslobj = sslctx.wrap_bio(incoming, outgoing, server_side=True)

            while True:
                try:
                    sslobj.do_handshake()
                except ssl.SSLWantReadError:
                    if outgoing.pending:
                        sock.send(outgoing.read())
                    incoming.write(sock.recv(16384))
                else:
                    if outgoing.pending:
                        sock.send(outgoing.read())
                    break

            while True:
                try:
                    data = sslobj.read(4)
                except ssl.SSLWantReadError:
                    incoming.write(sock.recv(16384))
                else:
                    break

            self.assertEqual(data, b'ping')
            sslobj.write(b'pong')
            sock.send(outgoing.read())

            time.sleep(0.2)  # wait for the peer to fill its backlog

            # send close_notify but don't wait for response
            with self.assertRaises(ssl.SSLWantReadError):
                sslobj.unwrap()
            sock.send(outgoing.read())

            # should receive all data
            data_len = 0
            while True:
                try:
                    chunk = len(sslobj.read(16384))
                    data_len += chunk
                except ssl.SSLWantReadError:
                    incoming.write(sock.recv(16384))
                except ssl.SSLZeroReturnError:
                    break

            self.assertEqual(data_len, CHUNK * SIZE*2)

            # verify that close_notify is received
            sslobj.unwrap()

            sock.close()