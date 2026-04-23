def _read_component_index(custom_path: str | None = None) -> dict | None:
    """Read and validate the prebuilt component index.

    Args:
        custom_path: Optional custom path or URL to index file. If None, uses built-in index.

    Returns:
        The index dictionary if valid, None otherwise
    """
    try:
        import lfx

        # Determine index location
        if custom_path:
            # Check if it's a URL
            if custom_path.startswith(("http://", "https://")):
                # Fetch from URL
                import httpx

                try:
                    response = httpx.get(custom_path, timeout=10.0)
                    response.raise_for_status()
                    blob = orjson.loads(response.content)
                except httpx.HTTPError as e:
                    logger.warning(f"Failed to fetch component index from {custom_path}: {e}")
                    return None
                except orjson.JSONDecodeError as e:
                    logger.warning(f"Component index from {custom_path} is corrupted or invalid JSON: {e}")
                    return None
            else:
                # Load from file path
                index_path = Path(custom_path)
                if not index_path.exists():
                    logger.warning(f"Custom component index not found at {custom_path}")
                    return None
                try:
                    blob = orjson.loads(index_path.read_bytes())
                except orjson.JSONDecodeError as e:
                    logger.warning(f"Component index at {custom_path} is corrupted or invalid JSON: {e}")
                    return None
        else:
            # Use built-in index
            pkg_dir = Path(inspect.getfile(lfx)).parent
            index_path = pkg_dir / "_assets" / "component_index.json"

            if not index_path.exists():
                return None

            try:
                blob = orjson.loads(index_path.read_bytes())
            except orjson.JSONDecodeError as e:
                logger.warning(f"Built-in component index is corrupted or invalid JSON: {e}")
                return None

        # Integrity check: verify SHA256
        tmp = dict(blob)
        sha = tmp.pop("sha256", None)
        if not sha:
            logger.warning("Component index missing SHA256 hash - index may be tampered")
            return None

        # Use orjson for hash calculation to match build script
        calc = hashlib.sha256(orjson.dumps(tmp, option=orjson.OPT_SORT_KEYS)).hexdigest()
        if sha != calc:
            logger.warning(
                "Component index integrity check failed - SHA256 mismatch (file may be corrupted or tampered)"
            )
            return None

        # Version check: ensure index matches installed lfx version
        from importlib.metadata import PackageNotFoundError, version

        try:
            installed_version = version("lfx")
        except PackageNotFoundError:
            # In some deployment environments (e.g. Docker with workspace installs),
            # lfx may be importable but lack dist-info metadata. Skip version check.
            logger.debug("Could not determine installed lfx version (no package metadata); skipping version check")
            installed_version = None

        if installed_version is not None and blob.get("version") != installed_version:
            logger.debug(
                f"Component index version mismatch: index={blob.get('version')}, installed={installed_version}"
            )
            return None
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Unexpected error reading component index: {type(e).__name__}: {e}")
        return None
    return blob