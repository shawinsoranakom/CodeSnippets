def ensure_converter_scripts(install_dir: Path, llama_tag: str) -> None:
    canonical = install_dir / "convert_hf_to_gguf.py"
    if not canonical.exists():
        # Hydrated source tree should have placed this file already.
        # Fall back to a network fetch so the install is not blocked.
        raw_base = f"https://raw.githubusercontent.com/ggml-org/llama.cpp/{llama_tag}"
        source_url = f"{raw_base}/convert_hf_to_gguf.py"
        data = download_bytes(
            source_url,
            progress_label = f"Downloading {download_label_from_url(source_url)}",
        )
        if not data:
            raise RuntimeError(f"downloaded empty converter script from {source_url}")
        if b"import " not in data and b"def " not in data and b"#!/" not in data:
            raise RuntimeError(
                f"downloaded converter script did not look like Python source: {source_url}"
            )
        atomic_write_bytes(canonical, data)
    legacy = install_dir / "convert-hf-to-gguf.py"
    if legacy.exists() or legacy.is_symlink():
        legacy.unlink()
    try:
        legacy.symlink_to("convert_hf_to_gguf.py")
    except OSError:
        shutil.copy2(canonical, legacy)