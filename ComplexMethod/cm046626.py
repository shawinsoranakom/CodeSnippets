def _download_gguf(
        self,
        *,
        hf_repo: str,
        hf_variant: Optional[str] = None,
        hf_token: Optional[str] = None,
    ) -> str:
        """Download GGUF file(s) from HuggingFace. Returns local path.

        Runs WITHOUT self._lock so that unload_model() can set
        _cancel_event at any time. Checks _cancel_event between
        each shard download.
        """
        try:
            from huggingface_hub import hf_hub_download
        except ImportError:
            raise RuntimeError(
                "huggingface_hub is required for HF model loading. "
                "Install it with: pip install huggingface_hub"
            )

        # Determine the filename from the variant
        gguf_filename = None
        gguf_extra_shards: list[str] = []
        if hf_variant:
            try:
                from huggingface_hub import list_repo_files

                files = list_repo_files(hf_repo, token = hf_token)
                variant_lower = hf_variant.lower()
                boundary = re.compile(
                    r"(?<![a-zA-Z0-9])" + re.escape(variant_lower) + r"(?![a-zA-Z0-9])"
                )
                gguf_files = sorted(
                    f
                    for f in files
                    if f.endswith(".gguf") and boundary.search(f.lower())
                )
                if gguf_files:
                    gguf_filename = gguf_files[0]
                    m = _SHARD_FULL_RE.match(gguf_filename)
                    if m:
                        prefix = m.group(1)
                        total = m.group(3)
                        sibling_pat = re.compile(
                            r"^"
                            + re.escape(prefix)
                            + r"-\d{5}-of-"
                            + re.escape(total)
                            + r"\.gguf$"
                        )
                        gguf_extra_shards = [
                            f for f in gguf_files[1:] if sibling_pat.match(f)
                        ]
            except Exception as e:
                logger.warning(f"Could not list repo files: {e}")

            if not gguf_filename:
                repo_name = hf_repo.split("/")[-1].replace("-GGUF", "")
                gguf_filename = f"{repo_name}-{hf_variant}.gguf"

        # Check disk space and fall back to a smaller variant if needed
        all_gguf_files = [gguf_filename] + gguf_extra_shards
        try:
            import os

            from huggingface_hub import get_paths_info, try_to_load_from_cache

            path_infos = list(get_paths_info(hf_repo, all_gguf_files, token = hf_token))
            total_bytes = sum((p.size or 0) for p in path_infos)

            # Subtract bytes already present in the HF cache so we only
            # preflight against what we actually have to download. Without
            # this, re-loading a cached large model (e.g. MiniMax-M2.7-GGUF
            # at 131 GB) fails cold whenever free disk is below the full
            # weight footprint, even though nothing needs downloading.
            already_cached_bytes = 0
            for p in path_infos:
                if not p.size:
                    continue
                try:
                    cached_path = try_to_load_from_cache(hf_repo, p.path)
                except Exception:
                    cached_path = None
                if isinstance(cached_path, str) and os.path.exists(cached_path):
                    try:
                        on_disk = os.path.getsize(cached_path)
                    except OSError:
                        on_disk = 0
                    # Count as satisfied only when the full blob is present.
                    if on_disk >= p.size:
                        already_cached_bytes += p.size

            total_download_bytes = max(0, total_bytes - already_cached_bytes)

            if total_download_bytes > 0:
                cache_dir = os.environ.get(
                    "HF_HUB_CACHE",
                    str(Path.home() / ".cache" / "huggingface" / "hub"),
                )
                Path(cache_dir).mkdir(parents = True, exist_ok = True)
                free_bytes = shutil.disk_usage(cache_dir).free

                total_gb = total_download_bytes / (1024**3)
                free_gb = free_bytes / (1024**3)
                cached_gb = already_cached_bytes / (1024**3)

                logger.info(
                    f"GGUF download: {total_gb:.1f} GB needed "
                    f"({cached_gb:.1f} GB already cached), "
                    f"{free_gb:.1f} GB free on disk"
                )

                if total_download_bytes > free_bytes:
                    smaller = self._find_smallest_fitting_variant(
                        hf_repo,
                        free_bytes,
                        hf_token,
                    )
                    if smaller:
                        fallback_file, fallback_size = smaller
                        logger.info(
                            f"Selected variant too large ({total_gb:.1f} GB), "
                            f"falling back to {fallback_file} ({fallback_size / (1024**3):.1f} GB)"
                        )
                        gguf_filename = fallback_file
                        _m = _SHARD_RE.match(gguf_filename)
                        _prefix = _m.group(1) if _m else None
                        if _prefix:
                            gguf_extra_shards = sorted(
                                f
                                for f in all_gguf_files
                                if f.startswith(_prefix)
                                and f != gguf_filename
                                and "mmproj" not in f.lower()
                            )
                        else:
                            gguf_extra_shards = []
                    else:
                        raise RuntimeError(
                            f"Not enough disk space to download any variant. "
                            f"Only {free_gb:.1f} GB free in {cache_dir}"
                        )
        except RuntimeError:
            raise
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")

        gguf_label = f"{hf_repo}/{gguf_filename}" + (
            f" (+{len(gguf_extra_shards)} shards)" if gguf_extra_shards else ""
        )
        logger.info(f"Resolving GGUF: {gguf_label}")
        try:
            if self._cancel_event.is_set():
                raise RuntimeError("Cancelled")
            dl_start = time.monotonic()
            local_path = hf_hub_download(
                repo_id = hf_repo,
                filename = gguf_filename,
                token = hf_token,
            )
            for shard in gguf_extra_shards:
                if self._cancel_event.is_set():
                    raise RuntimeError("Cancelled")
                logger.info(f"Resolving GGUF shard: {shard}")
                hf_hub_download(
                    repo_id = hf_repo,
                    filename = shard,
                    token = hf_token,
                )
        except RuntimeError as e:
            if "Cancelled" in str(e):
                raise
            raise RuntimeError(
                f"Failed to download GGUF file '{gguf_filename}' from {hf_repo}: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to download GGUF file '{gguf_filename}' from {hf_repo}: {e}"
            )

        dl_elapsed = time.monotonic() - dl_start
        if dl_elapsed < 2.0:
            logger.info(f"GGUF resolved from cache: {local_path}")
        else:
            logger.info(f"GGUF downloaded in {dl_elapsed:.1f}s: {local_path}")
        return local_path