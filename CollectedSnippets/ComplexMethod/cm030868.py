def test_recv_send(self):
        """Test recv(), send() and friends."""
        if support.verbose:
            sys.stdout.write("\n")

        server = ThreadedEchoServer(CERTFILE,
                                    certreqs=ssl.CERT_NONE,
                                    ssl_version=ssl.PROTOCOL_TLS_SERVER,
                                    cacerts=CERTFILE,
                                    chatty=True,
                                    connectionchatty=False)
        with server:
            s = test_wrap_socket(socket.socket(),
                                server_side=False,
                                certfile=CERTFILE,
                                ca_certs=CERTFILE,
                                cert_reqs=ssl.CERT_NONE)
            s.connect((HOST, server.port))
            # helper methods for standardising recv* method signatures
            def _recv_into():
                b = bytearray(b"\0"*100)
                count = s.recv_into(b)
                return b[:count]

            def _recvfrom_into():
                b = bytearray(b"\0"*100)
                count, addr = s.recvfrom_into(b)
                return b[:count]

            # (name, method, expect success?, *args, return value func)
            send_methods = [
                ('send', s.send, True, [], len),
                ('sendto', s.sendto, False, ["some.address"], len),
                ('sendall', s.sendall, True, [], lambda x: None),
            ]
            # (name, method, whether to expect success, *args)
            recv_methods = [
                ('recv', s.recv, True, []),
                ('recvfrom', s.recvfrom, False, ["some.address"]),
                ('recv_into', _recv_into, True, []),
                ('recvfrom_into', _recvfrom_into, False, []),
            ]
            data_prefix = "PREFIX_"

            for (meth_name, send_meth, expect_success, args,
                    ret_val_meth) in send_methods:
                indata = (data_prefix + meth_name).encode('ascii')
                try:
                    ret = send_meth(indata, *args)
                    msg = "sending with {}".format(meth_name)
                    self.assertEqual(ret, ret_val_meth(indata), msg=msg)
                    outdata = s.read()
                    if outdata != indata.lower():
                        self.fail(
                            "While sending with <<{name:s}>> bad data "
                            "<<{outdata:r}>> ({nout:d}) received; "
                            "expected <<{indata:r}>> ({nin:d})\n".format(
                                name=meth_name, outdata=outdata[:20],
                                nout=len(outdata),
                                indata=indata[:20], nin=len(indata)
                            )
                        )
                except ValueError as e:
                    if expect_success:
                        self.fail(
                            "Failed to send with method <<{name:s}>>; "
                            "expected to succeed.\n".format(name=meth_name)
                        )
                    if not str(e).startswith(meth_name):
                        self.fail(
                            "Method <<{name:s}>> failed with unexpected "
                            "exception message: {exp:s}\n".format(
                                name=meth_name, exp=e
                            )
                        )

            for meth_name, recv_meth, expect_success, args in recv_methods:
                indata = (data_prefix + meth_name).encode('ascii')
                try:
                    s.send(indata)
                    outdata = recv_meth(*args)
                    if outdata != indata.lower():
                        self.fail(
                            "While receiving with <<{name:s}>> bad data "
                            "<<{outdata:r}>> ({nout:d}) received; "
                            "expected <<{indata:r}>> ({nin:d})\n".format(
                                name=meth_name, outdata=outdata[:20],
                                nout=len(outdata),
                                indata=indata[:20], nin=len(indata)
                            )
                        )
                except ValueError as e:
                    if expect_success:
                        self.fail(
                            "Failed to receive with method <<{name:s}>>; "
                            "expected to succeed.\n".format(name=meth_name)
                        )
                    if not str(e).startswith(meth_name):
                        self.fail(
                            "Method <<{name:s}>> failed with unexpected "
                            "exception message: {exp:s}\n".format(
                                name=meth_name, exp=e
                            )
                        )
                    # consume data
                    s.read()

            # read(-1, buffer) is supported, even though read(-1) is not
            data = b"data"
            s.send(data)
            buffer = bytearray(len(data))
            self.assertEqual(s.read(-1, buffer), len(data))
            self.assertEqual(buffer, data)

            # sendall accepts bytes-like objects
            if ctypes is not None:
                ubyte = ctypes.c_ubyte * len(data)
                byteslike = ubyte.from_buffer_copy(data)
                s.sendall(byteslike)
                self.assertEqual(s.read(), data)

            # Make sure sendmsg et al are disallowed to avoid
            # inadvertent disclosure of data and/or corruption
            # of the encrypted data stream
            self.assertRaises(NotImplementedError, s.dup)
            self.assertRaises(NotImplementedError, s.sendmsg, [b"data"])
            self.assertRaises(NotImplementedError, s.recvmsg, 100)
            self.assertRaises(NotImplementedError,
                              s.recvmsg_into, [bytearray(100)])
            s.write(b"over\n")

            self.assertRaises(ValueError, s.recv, -1)
            self.assertRaises(ValueError, s.read, -1)

            s.close()