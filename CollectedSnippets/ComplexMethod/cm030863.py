def ssl_io_loop(self, sock, incoming, outgoing, func, *args, **kwargs):
        # A simple IO loop. Call func(*args) depending on the error we get
        # (WANT_READ or WANT_WRITE) move data between the socket and the BIOs.
        timeout = kwargs.get('timeout', support.SHORT_TIMEOUT)
        count = 0
        for _ in support.busy_retry(timeout):
            errno = None
            count += 1
            try:
                ret = func(*args)
            except ssl.SSLError as e:
                if e.errno not in (ssl.SSL_ERROR_WANT_READ,
                                   ssl.SSL_ERROR_WANT_WRITE):
                    raise
                errno = e.errno
            # Get any data from the outgoing BIO irrespective of any error, and
            # send it to the socket.
            buf = outgoing.read()
            sock.sendall(buf)
            # If there's no error, we're done. For WANT_READ, we need to get
            # data from the socket and put it in the incoming BIO.
            if errno is None:
                break
            elif errno == ssl.SSL_ERROR_WANT_READ:
                buf = sock.recv(32768)
                if buf:
                    incoming.write(buf)
                else:
                    incoming.write_eof()
        if support.verbose:
            sys.stdout.write("Needed %d calls to complete %s().\n"
                             % (count, func.__name__))
        return ret