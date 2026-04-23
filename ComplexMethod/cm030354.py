def __init__(self, address=None, family=None, backlog=1, authkey=None):
        family = family or (address and address_type(address)) \
                 or default_family
        _validate_family(family)
        if authkey is not None and not isinstance(authkey, bytes):
            raise TypeError('authkey should be a byte string')

        if family == 'AF_PIPE':
            if address:
                self._listener = PipeListener(address, backlog)
            else:
                for attempts in itertools.count():
                    address = arbitrary_address(family)
                    try:
                        self._listener = PipeListener(address, backlog)
                        break
                    except OSError as e:
                        if attempts >= _MAX_PIPE_ATTEMPTS:
                            raise
                        if e.winerror not in (_winapi.ERROR_PIPE_BUSY,
                                              _winapi.ERROR_ACCESS_DENIED):
                            raise
        else:
            address = address or arbitrary_address(family)
            self._listener = SocketListener(address, family, backlog)

        self._authkey = authkey