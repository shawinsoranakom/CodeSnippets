def urljoin(base, path):
    if isinstance(path, bytes):
        path = path.decode()
    if not isinstance(path, str) or not path:
        return None
    if re.match(r'(?:[a-zA-Z][a-zA-Z0-9+-.]*:)?//', path):
        return path
    if isinstance(base, bytes):
        base = base.decode()
    if not isinstance(base, str) or not re.match(
            r'^(?:https?:)?//', base):
        return None
    return urllib.parse.urljoin(base, path)