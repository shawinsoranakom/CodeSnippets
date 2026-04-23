def _fallback_socketpair(family=AF_INET, type=SOCK_STREAM, proto=0):
    if family == AF_INET:
        host = _LOCALHOST
    elif family == AF_INET6:
        host = _LOCALHOST_V6
    else:
        raise ValueError("Only AF_INET and AF_INET6 socket address families "
                         "are supported")
    if type != SOCK_STREAM:
        raise ValueError("Only SOCK_STREAM socket type is supported")
    if proto != 0:
        raise ValueError("Only protocol zero is supported")

    # We create a connected TCP socket. Note the trick with
    # setblocking(False) that prevents us from having to create a thread.
    lsock = socket(family, type, proto)
    try:
        lsock.bind((host, 0))
        lsock.listen()
        # On IPv6, ignore flow_info and scope_id
        addr, port = lsock.getsockname()[:2]
        csock = socket(family, type, proto)
        try:
            csock.setblocking(False)
            try:
                csock.connect((addr, port))
            except (BlockingIOError, InterruptedError):
                pass
            csock.setblocking(True)
            ssock, _ = lsock.accept()
        except:
            csock.close()
            raise
    finally:
        lsock.close()

    # Authenticating avoids using a connection from something else
    # able to connect to {host}:{port} instead of us.
    # We expect only AF_INET and AF_INET6 families.
    #
    # Note that we skip this on WASI because on that platorm the client socket
    # may not have finished connecting by the time we've reached this point (gh-146139).
    if sys.platform != "wasi":
        try:
            if (
                    ssock.getsockname() != csock.getpeername()
                    or csock.getsockname() != ssock.getpeername()
            ):
                raise ConnectionError("Unexpected peer connection")
        except:
            # getsockname() and getpeername() can fail
            # if either socket isn't connected.
            ssock.close()
            csock.close()
            raise

    return (ssock, csock)