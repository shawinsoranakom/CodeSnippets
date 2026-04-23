def run(self):
        if not self._in_context:
            raise ValueError(
                'ThreadedEchoServer must be used as a context manager')
        self.sock.settimeout(1.0)
        self.sock.listen(5)
        self.active = True
        if self.flag:
            # signal an event
            self.flag.set()
        while self.active:
            try:
                newconn, connaddr = self.sock.accept()
                if support.verbose and self.chatty:
                    sys.stdout.write(' server:  new connection from '
                                     + repr(connaddr) + '\n')
                handler = self.ConnectionHandler(self, newconn, connaddr)
                handler.start()
                handler.join()
            except TimeoutError as e:
                if support.verbose:
                    sys.stdout.write(f' connection timeout {e!r}\n')
            except KeyboardInterrupt:
                self.stop()
            except BaseException as e:
                if support.verbose and self.chatty:
                    sys.stdout.write(
                        ' connection handling failed: ' + repr(e) + '\n')

        self.close()