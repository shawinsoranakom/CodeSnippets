def __init__(self, uri: str):
        if not uri.startswith("ftp://"):
            raise ValueError(f"Incorrect URI scheme in {uri}, expected 'ftp'")
        u = urlparse(uri)
        assert u.port
        assert u.hostname
        self.port: int = u.port
        self.host: str = u.hostname
        self.port = int(u.port or 21)
        assert self.FTP_USERNAME
        assert self.FTP_PASSWORD
        self.username: str = u.username or self.FTP_USERNAME
        self.password: str = u.password or self.FTP_PASSWORD
        self.basedir: str = u.path.rstrip("/")