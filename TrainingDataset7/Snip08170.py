def load_manifest(self):
        content = self.read_manifest()
        if content is None:
            return {}, ""
        try:
            stored = json.loads(content)
        except json.JSONDecodeError:
            pass
        else:
            version = stored.get("version")
            if version in ("1.0", "1.1"):
                return stored.get("paths", {}), stored.get("hash", "")
        raise ValueError(
            "Couldn't load manifest '%s' (version %s)"
            % (self.manifest_name, self.manifest_version)
        )