def _get_hostport(self, host, port):
        if port is None:
            i = host.rfind(':')
            j = host.rfind(']')         # ipv6 addresses have [...]
            if i > j:
                try:
                    port = int(host[i+1:])
                except ValueError:
                    if host[i+1:] == "": # http://foo.com:/ == http://foo.com/
                        port = self.default_port
                    else:
                        raise InvalidURL("nonnumeric port: '%s'" % host[i+1:])
                host = host[:i]
            else:
                port = self.default_port
        if host and host[0] == '[' and host[-1] == ']':
            host = host[1:-1]

        return (host, port)