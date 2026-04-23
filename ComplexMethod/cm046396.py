def origin(self) -> str | None:
        """Origin URL or None."""
        if not self.is_repo:
            return None
        cfg = self.gitdir / "config"
        remote, url = None, None
        for s in (self._read(cfg) or "").splitlines():
            t = s.strip()
            if t.startswith("[") and t.endswith("]"):
                remote = t.lower()
            elif t.lower().startswith("url =") and remote == '[remote "origin"]':
                url = t.split("=", 1)[1].strip()
                break
        return url