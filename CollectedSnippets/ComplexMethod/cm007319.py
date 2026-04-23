def _create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
            host, port = address
            err = None
            addrs = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
            af = socket.AF_INET if '.' in source_address[0] else socket.AF_INET6
            ip_addrs = [addr for addr in addrs if addr[0] == af]
            if addrs and not ip_addrs:
                ip_version = 'v4' if af == socket.AF_INET else 'v6'
                raise socket.error(
                    "No remote IP%s addresses available for connect, can't use '%s' as source address"
                    % (ip_version, source_address[0]))
            for res in ip_addrs:
                af, socktype, proto, canonname, sa = res
                sock = None
                try:
                    sock = socket.socket(af, socktype, proto)
                    if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                        sock.settimeout(timeout)
                    sock.bind(source_address)
                    sock.connect(sa)
                    err = None  # Explicitly break reference cycle
                    return sock
                except socket.error as _:
                    err = _
                    if sock is not None:
                        sock.close()
            if err is not None:
                raise err
            else:
                raise socket.error('getaddrinfo returns an empty list')