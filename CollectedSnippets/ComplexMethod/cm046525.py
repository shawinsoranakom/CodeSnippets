def _scan_ollama_dir(
    ollama_dir: Path, limit: Optional[int] = None
) -> List[LocalModelInfo]:
    """Scan an Ollama models directory for downloaded models.

    Ollama stores models in a content-addressable layout::

        <ollama_dir>/manifests/<host>/<namespace>/<model>/<tag>
        <ollama_dir>/blobs/sha256-...

    The default host is ``registry.ollama.ai`` with namespace
    ``library`` (official models), but users can pull from custom
    namespaces (``mradermacher/llama3``) or entirely different hosts
    (``hf.co/org/repo:tag``).  We iterate all manifest files via
    ``rglob`` so every layout depth is discovered.

    Each manifest is JSON with a ``layers`` array. The layer with
    ``mediaType == "application/vnd.ollama.image.model"`` contains the
    GGUF weights. Vision models also have a projector layer
    (``application/vnd.ollama.image.projector``). We read the config
    layer to extract family/size info.

    Since Ollama blobs lack a ``.gguf`` extension (which the GGUF
    loading pipeline requires), we create ``.gguf``-named links
    pointing at the blobs so the existing ``detect_gguf_model`` and
    ``llama-server -m`` paths work unchanged. Each model gets its
    own subdirectory under the links dir (keyed by a short hash of
    the manifest path) so that ``detect_mmproj_file`` only sees the
    projector for *that* model.  Links are created as symlinks when
    possible, falling back to hardlinks (Windows without Developer
    Mode) as a last resort.  The link dir lives under
    ``<ollama_dir>/.studio_links/`` when writable, otherwise under
    Studio's own cache directory.
    """
    manifests_root = ollama_dir / "manifests"
    if not manifests_root.is_dir():
        return []

    found: List[LocalModelInfo] = []
    blobs_dir = ollama_dir / "blobs"
    links_root = _ollama_links_dir(ollama_dir)
    if links_root is None:
        logger.warning(
            "Skipping Ollama scan for %s: no writable location for .gguf links",
            ollama_dir,
        )
        return []

    def _make_link(link_dir: Path, link_name: str, target: Path) -> Optional[str]:
        """Create a .gguf-named link to an Ollama blob.

        Tries symlink first, then hardlink (works on Windows without
        Developer Mode when target is on the same filesystem).  Skips
        the model if neither works -- a full file copy of a multi-GB
        GGUF inside a synchronous API request would block the backend.

        Idempotent: skips recreation when a valid link already exists.
        """
        link_dir.mkdir(parents = True, exist_ok = True)
        link_path = link_dir / link_name
        resolved = target.resolve()

        # Skip if the link already points at the exact same blob.
        # Only use samefile -- size-based checks can reuse stale links
        # after `ollama pull` updates a tag to a same-sized blob.
        try:
            if link_path.exists() and os.path.samefile(str(link_path), str(resolved)):
                return str(link_path)
        except OSError as e:
            logger.debug("Error checking existing link %s: %s", link_path, e)

        tmp_path = link_dir / f".{link_name}.tmp-{uuid.uuid4().hex[:8]}"
        try:
            if tmp_path.is_symlink() or tmp_path.exists():
                tmp_path.unlink()
            try:
                tmp_path.symlink_to(resolved)
            except OSError:
                try:
                    os.link(str(resolved), str(tmp_path))
                except OSError:
                    logger.warning(
                        "Could not create link for Ollama blob %s "
                        "(symlinks and hardlinks both failed). "
                        "Skipping model to avoid blocking the API.",
                        target,
                    )
                    return None
            os.replace(str(tmp_path), str(link_path))
            return str(link_path)
        except OSError as e:
            logger.debug("Could not create Ollama link %s: %s", link_path, e)
            try:
                if tmp_path.is_symlink() or tmp_path.exists():
                    tmp_path.unlink()
            except OSError as cleanup_err:
                logger.debug(
                    "Could not clean up tmp path %s: %s", tmp_path, cleanup_err
                )
            return None

    try:
        for tag_file in manifests_root.rglob("*"):
            if not tag_file.is_file():
                continue

            rel = tag_file.relative_to(manifests_root)
            parts = rel.parts
            if len(parts) < 3:
                continue

            host = parts[0]
            repo_parts = list(parts[1:-1])
            tag = parts[-1]

            if (
                host == "registry.ollama.ai"
                and repo_parts
                and repo_parts[0] == "library"
            ):
                repo_name = "/".join(repo_parts[1:])
            elif host == "registry.ollama.ai":
                repo_name = "/".join(repo_parts)
            else:
                repo_name = "/".join([host] + repo_parts)

            if not repo_name:
                continue

            display = f"{repo_name}:{tag}"

            manifest_key = rel.as_posix()
            stem_hash = hashlib.sha256(manifest_key.encode()).hexdigest()[:10]

            try:
                manifest = json.loads(tag_file.read_text())
            except (json.JSONDecodeError, OSError) as e:
                logger.debug(
                    "Skipping unreadable/invalid Ollama manifest %s: %s",
                    tag_file,
                    e,
                )
                continue

            config_digest = manifest.get("config", {}).get("digest", "")
            model_type = ""
            file_type = ""
            if config_digest and blobs_dir.is_dir():
                config_blob = blobs_dir / config_digest.replace(":", "-")
                if config_blob.is_file():
                    try:
                        cfg = json.loads(config_blob.read_text())
                        model_type = cfg.get("model_type", "")
                        file_type = cfg.get("file_type", "")
                    except (json.JSONDecodeError, OSError) as e:
                        logger.debug(
                            "Could not parse Ollama config blob %s: %s",
                            config_blob,
                            e,
                        )

            model_link_dir = links_root / stem_hash

            gguf_link_path: Optional[str] = None
            quant = f"-{file_type}" if file_type else ""
            safe_name = repo_name.replace("/", "-")
            for layer in manifest.get("layers", []):
                media = layer.get("mediaType", "")
                digest = layer.get("digest", "")
                if not digest:
                    continue

                if media == "application/vnd.ollama.image.model":
                    candidate = blobs_dir / digest.replace(":", "-")
                    if candidate.is_file():
                        link_name = f"{safe_name}-{tag}{quant}.gguf"
                        gguf_link_path = _make_link(
                            model_link_dir, link_name, candidate
                        )

                elif media == "application/vnd.ollama.image.projector":
                    candidate = blobs_dir / digest.replace(":", "-")
                    if candidate.is_file():
                        mmproj_name = f"{safe_name}-{tag}-mmproj.gguf"
                        _make_link(model_link_dir, mmproj_name, candidate)

            if not gguf_link_path:
                continue

            suffix = ""
            if model_type:
                suffix += f" ({model_type}"
                if file_type:
                    suffix += f" {file_type}"
                suffix += ")"

            try:
                updated_at = tag_file.stat().st_mtime
            except OSError:
                updated_at = None

            found.append(
                LocalModelInfo(
                    id = gguf_link_path,
                    model_id = f"ollama/{repo_name}:{tag}",
                    display_name = display + suffix,
                    path = gguf_link_path,
                    source = "custom",
                    updated_at = updated_at,
                ),
            )
            if limit is not None and len(found) >= limit:
                return found
    except OSError as e:
        logger.warning("Error scanning Ollama directory %s: %s", ollama_dir, e)
    return found