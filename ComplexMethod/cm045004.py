def load(cls, key: str, project_root: Path) -> IntegrationManifest:
        """Load an existing manifest from disk.

        Raises ``FileNotFoundError`` if the manifest does not exist.
        """
        inst = cls(key, project_root)
        path = inst.manifest_path
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Integration manifest at {path} contains invalid JSON"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                f"Integration manifest at {path} must be a JSON object, "
                f"got {type(data).__name__}"
            )

        files = data.get("files", {})
        if not isinstance(files, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in files.items()
        ):
            raise ValueError(
                f"Integration manifest 'files' at {path} must be a "
                "mapping of string paths to string hashes"
            )

        inst.version = data.get("version", "")
        inst._installed_at = data.get("installed_at", "")
        inst._files = files

        stored_key = data.get("integration", "")
        if stored_key and stored_key != key:
            raise ValueError(
                f"Manifest at {path} belongs to integration {stored_key!r}, "
                f"not {key!r}"
            )

        return inst