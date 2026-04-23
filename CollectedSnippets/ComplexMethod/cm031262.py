async def _connect_sock(self, exceptions, addr_info, local_addr_infos=None):
        """Create, bind and connect one socket."""
        my_exceptions = []
        exceptions.append(my_exceptions)
        family, type_, proto, _, address = addr_info
        sock = None
        try:
            try:
                sock = socket.socket(family=family, type=type_, proto=proto)
                sock.setblocking(False)
                if local_addr_infos is not None:
                    for lfamily, _, _, _, laddr in local_addr_infos:
                        # skip local addresses of different family
                        if lfamily != family:
                            continue
                        try:
                            sock.bind(laddr)
                            break
                        except OSError as exc:
                            msg = (
                                f'error while attempting to bind on '
                                f'address {laddr!r}: {str(exc).lower()}'
                            )
                            exc = OSError(exc.errno, msg)
                            my_exceptions.append(exc)
                    else:  # all bind attempts failed
                        if my_exceptions:
                            raise my_exceptions.pop()
                        else:
                            raise OSError(f"no matching local address with {family=} found")
                await self.sock_connect(sock, address)
                return sock
            except OSError as exc:
                my_exceptions.append(exc)
                raise
        except:
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    # An error when closing a newly created socket is
                    # not important, but it can overwrite more important
                    # non-OSError error. So ignore it.
                    pass
            raise
        finally:
            exceptions = my_exceptions = None