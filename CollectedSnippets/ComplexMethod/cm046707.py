def clear_unsloth_compiled_cache(preserve_patterns: Optional[List[str]] = None) -> None:
    """
    Remove compiled files from the cache directory (idempotent).

    Args:
        preserve_patterns: A list of glob patterns for files to keep
                           (e.g., ["Unsloth*Trainer.py"]). If None or empty,
                           the entire cache directory is deleted (legacy behavior).
    """
    for cache_dir in _CACHE_DIRS:
        if not cache_dir.exists():
            continue

        if preserve_patterns:
            logger.info(
                f"Cleaning unsloth compiled cache (preserving {preserve_patterns}): "
                f"{cache_dir}"
            )

            for item in cache_dir.iterdir():
                if item.is_file():
                    # Check if the file matches any of the patterns we want to keep
                    preserve = any(item.match(pattern) for pattern in preserve_patterns)
                    if not preserve:
                        try:
                            item.unlink()
                        except OSError as e:
                            logger.debug(f"Could not delete {item}: {e}")

                elif item.is_dir():
                    # Always clear __pycache__ and other subdirectories
                    shutil.rmtree(item, ignore_errors = True)
        else:
            # Legacy behavior: nuke the entire directory
            logger.info(f"Removing unsloth compiled cache: {cache_dir}")
            shutil.rmtree(cache_dir, ignore_errors = True)