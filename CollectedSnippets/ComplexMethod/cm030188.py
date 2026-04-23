def _sendfile_zerocopy(self, zerocopy_func, giveup_exc_type, file,
                           offset=0, count=None):
        """
        Send a file using a zero-copy function.
        """
        import selectors

        self._check_sendfile_params(file, offset, count)
        sockno = self.fileno()
        try:
            fileno = file.fileno()
        except (AttributeError, io.UnsupportedOperation) as err:
            raise giveup_exc_type(err)  # not a regular file
        try:
            fsize = os.fstat(fileno).st_size
        except OSError as err:
            raise giveup_exc_type(err)  # not a regular file
        if not fsize:
            return 0  # empty file
        # Truncate to 1GiB to avoid OverflowError, see bpo-38319.
        blocksize = min(count or fsize, 2 ** 30)
        timeout = self.gettimeout()
        if timeout == 0:
            raise ValueError("non-blocking sockets are not supported")
        # poll/select have the advantage of not requiring any
        # extra file descriptor, contrarily to epoll/kqueue
        # (also, they require a single syscall).
        if hasattr(selectors, 'PollSelector'):
            selector = selectors.PollSelector()
        else:
            selector = selectors.SelectSelector()
        selector.register(sockno, selectors.EVENT_WRITE)

        total_sent = 0
        # localize variable access to minimize overhead
        selector_select = selector.select
        try:
            while True:
                if timeout and not selector_select(timeout):
                    raise TimeoutError('timed out')
                if count:
                    blocksize = min(count - total_sent, blocksize)
                    if blocksize <= 0:
                        break
                try:
                    sent = zerocopy_func(fileno, offset, blocksize)
                except BlockingIOError:
                    if not timeout:
                        # Block until the socket is ready to send some
                        # data; avoids hogging CPU resources.
                        selector_select()
                    continue
                except OSError as err:
                    if total_sent == 0:
                        # We can get here for different reasons, the main
                        # one being 'file' is not a regular mmap(2)-like
                        # file, in which case we'll fall back on using
                        # plain send().
                        raise giveup_exc_type(err)
                    raise err from None
                else:
                    if sent == 0:
                        break  # EOF
                    offset += sent
                    total_sent += sent
            return total_sent
        finally:
            if total_sent > 0 and hasattr(file, 'seek'):
                file.seek(offset)