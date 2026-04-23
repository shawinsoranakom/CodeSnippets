def get_host_from_link(link: str) -> str:

    host = link.split('://', 1)[1] if '://' in link else link

    # Remove routes, arguments and anchors
    if '/' in host:
        host = host.split('/', 1)[0]

    elif '?' in host:
        host = host.split('?', 1)[0]

    elif '#' in host:
        host = host.split('#', 1)[0]

    return host
