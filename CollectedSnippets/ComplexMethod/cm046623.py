def _find_smallest_fitting_variant(
        hf_repo: str,
        free_bytes: int,
        hf_token: Optional[str] = None,
    ) -> Optional[tuple[str, int]]:
        """Find the smallest GGUF variant (including all shards) that fits.

        Groups split shards by variant prefix and sums their sizes.
        For example, UD-Q4_K_XL with 9 shards of 50 GB each = 450 GB total.

        Returns (first_shard_filename, total_size_bytes) or None if nothing fits.
        """
        try:
            from huggingface_hub import get_paths_info, list_repo_files

            files = list_repo_files(hf_repo, token = hf_token)
            gguf_files = [
                f for f in files if f.endswith(".gguf") and "mmproj" not in f.lower()
            ]
            if not gguf_files:
                return None

            # Get sizes for all GGUF files
            path_infos = list(get_paths_info(hf_repo, gguf_files, token = hf_token))
            size_map = {p.path: (p.size or 0) for p in path_infos}

            # Group files by variant: shards share a prefix before -NNNNN-of-NNNNN
            variants: dict[str, list[str]] = {}
            for f in gguf_files:
                m = _SHARD_RE.match(f)
                key = m.group(1) if m else f
                variants.setdefault(key, []).append(f)

            # Sum shard sizes per variant, track the first shard (for download)
            variant_sizes: list[tuple[str, int, list[str]]] = []
            for key, shard_files in variants.items():
                total = sum(size_map.get(f, 0) for f in shard_files)
                first = sorted(shard_files)[0]
                variant_sizes.append((first, total, shard_files))

            # Sort by total size ascending and pick the smallest that fits
            variant_sizes.sort(key = lambda x: x[1])
            for first_file, total_size, _ in variant_sizes:
                if total_size > 0 and total_size <= free_bytes:
                    return first_file, total_size

            return None
        except Exception:
            return None