def hydrate_source_tree(
    source_ref: str,
    install_dir: Path,
    work_dir: Path,
    *,
    source_repo: str = UPSTREAM_REPO,
    expected_sha256: str | None,
    source_label: str | None = None,
    exact_source: bool = False,
) -> None:
    archive_path = work_dir / f"llama.cpp-source-{source_ref}.tar.gz"
    source_urls = (
        commit_source_archive_urls(source_repo, source_ref)
        if exact_source
        else upstream_source_archive_urls(source_ref)
    )
    label = source_label or f"llama.cpp source tree for {source_ref}"
    extract_dir = Path(tempfile.mkdtemp(prefix = "source-extract-", dir = work_dir))

    try:
        log(f"downloading {label}")
        last_exc: Exception | None = None
        downloaded = False
        for index, source_url in enumerate(source_urls):
            try:
                if index > 0:
                    log(
                        f"retrying source tree download from fallback URL: {source_url}"
                    )
                download_file_verified(
                    source_url,
                    archive_path,
                    expected_sha256 = expected_sha256,
                    label = label,
                )
                downloaded = True
                break
            except Exception as exc:
                last_exc = exc
                if index == len(source_urls) - 1:
                    raise
                log(f"source tree download failed from {source_url}: {exc}")
        if not downloaded:
            assert last_exc is not None
            raise last_exc
        extract_archive(archive_path, extract_dir)
        source_root = extracted_archive_root(extract_dir)
        required_paths = [
            source_root / "CMakeLists.txt",
            source_root / "convert_hf_to_gguf.py",
            source_root / "gguf-py",
        ]
        missing = [
            str(path.relative_to(source_root))
            for path in required_paths
            if not path.exists()
        ]
        if missing:
            raise PrebuiltFallback(
                "upstream source archive was missing required repo files: "
                + ", ".join(missing)
            )
        copy_directory_contents(source_root, install_dir)
    except PrebuiltFallback:
        raise
    except Exception as exc:
        raise PrebuiltFallback(f"failed to hydrate {label}: {exc}") from exc
    finally:
        remove_tree(extract_dir)