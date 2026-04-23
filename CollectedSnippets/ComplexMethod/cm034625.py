def is_safe_url(url: str) -> bool:
    """Return True only for http/https URLs that do not point to private/loopback/reserved addresses."""
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False

        if "\\" in url:
            return False

        hostname = parsed.hostname
        if hostname is None:
            return False

        if urllib3_parse_url is not None:
            parsed_urllib3 = urllib3_parse_url(url)
            if parsed_urllib3.host and parsed_urllib3.host != hostname:
                return False
            hostname = parsed_urllib3.host or hostname

        if hostname is None:
            return False

        addr_infos = socket.getaddrinfo(hostname, None)
        if not addr_infos:
            return False

        for addr_info in addr_infos:
            addr = ipaddress.ip_address(addr_info[4][0])
            if (addr.is_private or addr.is_loopback or addr.is_link_local
                    or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
                return False
    except Exception:
        return False
    return True