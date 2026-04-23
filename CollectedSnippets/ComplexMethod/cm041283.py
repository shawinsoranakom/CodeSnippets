def is_port_open(
    port_or_url: int | str,
    http_path: str = None,
    expect_success: bool = True,
    protocols: str | list[str] | None = None,
    quiet: bool = True,
):
    from localstack.utils.http import safe_requests

    protocols = protocols or ["tcp"]
    port = port_or_url
    if is_number(port):
        port = int(port)
    host = "localhost"
    protocol = "http"
    protocols = protocols if isinstance(protocols, list) else [protocols]
    if isinstance(port, str):
        url = urlparse(port_or_url)
        port = url.port
        host = url.hostname
        protocol = url.scheme
    nw_protocols = []
    nw_protocols += [socket.SOCK_STREAM] if "tcp" in protocols else []
    nw_protocols += [socket.SOCK_DGRAM] if "udp" in protocols else []
    for nw_protocol in nw_protocols:
        with closing(
            socket.socket(socket.AF_INET if ":" not in host else socket.AF_INET6, nw_protocol)
        ) as sock:
            sock.settimeout(1)
            if nw_protocol == socket.SOCK_DGRAM:
                try:
                    if port == 53:
                        dnshost = "127.0.0.1" if host == "localhost" else host
                        resolver = dns.resolver.Resolver()
                        resolver.nameservers = [dnshost]
                        resolver.timeout = 1
                        resolver.lifetime = 1
                        answers = resolver.query("google.com", "A")
                        assert len(answers) > 0
                    else:
                        sock.sendto(b"", (host, port))
                        sock.recvfrom(1024)
                except Exception:
                    if not quiet:
                        LOG.error(
                            "Error connecting to UDP port %s:%s",
                            host,
                            port,
                            exc_info=LOG.isEnabledFor(logging.DEBUG),
                        )
                    return False
            elif nw_protocol == socket.SOCK_STREAM:
                result = sock.connect_ex((host, port))
                if result != 0:
                    if not quiet:
                        LOG.warning(
                            "Error connecting to TCP port %s:%s (result=%s)", host, port, result
                        )
                    return False
    if "tcp" not in protocols or not http_path:
        return True
    host = f"[{host}]" if ":" in host else host
    url = f"{protocol}://{host}:{port}{http_path}"
    try:
        response = safe_requests.get(url, verify=False)
        return not expect_success or response.status_code < 400
    except Exception:
        return False