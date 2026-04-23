def test_starttls(self):
        """Switching from clear text to encrypted and back again."""
        msgs = (b"msg 1", b"MSG 2", b"STARTTLS", b"MSG 3", b"msg 4", b"ENDTLS", b"msg 5", b"msg 6")

        server = ThreadedEchoServer(CERTFILE,
                                    starttls_server=True,
                                    chatty=True,
                                    connectionchatty=True)
        wrapped = False
        with server:
            s = socket.socket()
            s.setblocking(True)
            s.connect((HOST, server.port))
            if support.verbose:
                sys.stdout.write("\n")
            for indata in msgs:
                if support.verbose:
                    sys.stdout.write(
                        " client:  sending %r...\n" % indata)
                if wrapped:
                    conn.write(indata)
                    outdata = conn.read()
                else:
                    s.send(indata)
                    outdata = s.recv(1024)
                msg = outdata.strip().lower()
                if indata == b"STARTTLS" and msg.startswith(b"ok"):
                    # STARTTLS ok, switch to secure mode
                    if support.verbose:
                        sys.stdout.write(
                            " client:  read %r from server, starting TLS...\n"
                            % msg)
                    conn = test_wrap_socket(s)
                    wrapped = True
                elif indata == b"ENDTLS" and msg.startswith(b"ok"):
                    # ENDTLS ok, switch back to clear text
                    if support.verbose:
                        sys.stdout.write(
                            " client:  read %r from server, ending TLS...\n"
                            % msg)
                    s = conn.unwrap()
                    wrapped = False
                else:
                    if support.verbose:
                        sys.stdout.write(
                            " client:  read %r from server\n" % msg)
            if support.verbose:
                sys.stdout.write(" client:  closing connection.\n")
            if wrapped:
                conn.write(b"over\n")
            else:
                s.send(b"over\n")
            if wrapped:
                conn.close()
            else:
                s.close()