def _sock_sendfile_native_impl(self, fut, registered_fd, sock, fileno,
                                   offset, count, blocksize, total_sent):
        fd = sock.fileno()
        if registered_fd is not None:
            # Remove the callback early.  It should be rare that the
            # selector says the fd is ready but the call still returns
            # EAGAIN, and I am willing to take a hit in that case in
            # order to simplify the common case.
            self.remove_writer(registered_fd)
        if fut.cancelled():
            self._sock_sendfile_update_filepos(fileno, offset, total_sent)
            return
        if count:
            blocksize = count - total_sent
            if blocksize <= 0:
                self._sock_sendfile_update_filepos(fileno, offset, total_sent)
                fut.set_result(total_sent)
                return

        # On 32-bit architectures truncate to 1GiB to avoid OverflowError
        blocksize = min(blocksize, sys.maxsize//2 + 1)

        try:
            sent = os.sendfile(fd, fileno, offset, blocksize)
        except (BlockingIOError, InterruptedError):
            if registered_fd is None:
                self._sock_add_cancellation_callback(fut, sock)
            self.add_writer(fd, self._sock_sendfile_native_impl, fut,
                            fd, sock, fileno,
                            offset, count, blocksize, total_sent)
        except OSError as exc:
            if (registered_fd is not None and
                    exc.errno == errno.ENOTCONN and
                    type(exc) is not ConnectionError):
                # If we have an ENOTCONN and this isn't a first call to
                # sendfile(), i.e. the connection was closed in the middle
                # of the operation, normalize the error to ConnectionError
                # to make it consistent across all Posix systems.
                new_exc = ConnectionError(
                    "socket is not connected", errno.ENOTCONN)
                new_exc.__cause__ = exc
                exc = new_exc
            if total_sent == 0:
                # We can get here for different reasons, the main
                # one being 'file' is not a regular mmap(2)-like
                # file, in which case we'll fall back on using
                # plain send().
                err = exceptions.SendfileNotAvailableError(
                    "os.sendfile call failed")
                self._sock_sendfile_update_filepos(fileno, offset, total_sent)
                fut.set_exception(err)
            else:
                self._sock_sendfile_update_filepos(fileno, offset, total_sent)
                fut.set_exception(exc)
        except (SystemExit, KeyboardInterrupt):
            raise
        except BaseException as exc:
            self._sock_sendfile_update_filepos(fileno, offset, total_sent)
            fut.set_exception(exc)
        else:
            if sent == 0:
                # EOF
                self._sock_sendfile_update_filepos(fileno, offset, total_sent)
                fut.set_result(total_sent)
            else:
                offset += sent
                total_sent += sent
                if registered_fd is None:
                    self._sock_add_cancellation_callback(fut, sock)
                self.add_writer(fd, self._sock_sendfile_native_impl, fut,
                                fd, sock, fileno,
                                offset, count, blocksize, total_sent)