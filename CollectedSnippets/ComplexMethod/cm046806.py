def test_validate_prebuilt_choice_creates_repo_shaped_windows_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    upstream_tag = "b9997"
    bundle_name = "app-b9997-windows-x64-cpu.zip"
    source_archive = tmp_path / "source.tar.gz"
    bundle_archive = tmp_path / "bundle.zip"
    with tarfile.open(source_archive, "w:gz") as archive:
        add_bytes_to_tar(
            archive,
            f"llama.cpp-{upstream_tag}/CMakeLists.txt",
            b"cmake_minimum_required(VERSION 3.14)\n",
        )
        add_bytes_to_tar(
            archive,
            f"llama.cpp-{upstream_tag}/convert_hf_to_gguf.py",
            b"#!/usr/bin/env python3\nimport gguf\n",
        )
        add_bytes_to_tar(
            archive,
            f"llama.cpp-{upstream_tag}/gguf-py/gguf/__init__.py",
            b"__all__ = []\n",
        )
    with zipfile.ZipFile(bundle_archive, "w") as archive:
        archive.writestr("llama-server.exe", b"MZ")
        archive.writestr("llama-quantize.exe", b"MZ")
        archive.writestr("llama.dll", b"DLL")
        archive.writestr("BUILD_INFO.txt", b"bundle metadata\n")

    source_urls = set(INSTALL_LLAMA_PREBUILT.upstream_source_archive_urls(upstream_tag))

    def fake_download_file(url: str, destination: Path) -> None:
        if url in source_urls:
            destination.write_bytes(source_archive.read_bytes())
            return
        if url == "file://bundle.zip":
            destination.write_bytes(bundle_archive.read_bytes())
            return
        raise AssertionError(f"unexpected download url: {url}")

    monkeypatch.setattr(INSTALL_LLAMA_PREBUILT, "download_file", fake_download_file)
    monkeypatch.setattr(
        INSTALL_LLAMA_PREBUILT,
        "download_bytes",
        lambda url, **_: b"#!/usr/bin/env python3\nimport gguf\n",
    )
    monkeypatch.setattr(
        INSTALL_LLAMA_PREBUILT,
        "preflight_linux_installed_binaries",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        INSTALL_LLAMA_PREBUILT, "validate_quantize", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        INSTALL_LLAMA_PREBUILT, "validate_server", lambda *args, **kwargs: None
    )

    host = HostInfo(
        system = "Windows",
        machine = "AMD64",
        is_windows = True,
        is_linux = False,
        is_macos = False,
        is_x86_64 = True,
        is_arm64 = False,
        nvidia_smi = None,
        driver_cuda_version = None,
        compute_caps = [],
        visible_cuda_devices = None,
        has_physical_nvidia = False,
        has_usable_nvidia = False,
    )
    choice = AssetChoice(
        repo = "local",
        tag = upstream_tag,
        name = bundle_name,
        url = "file://bundle.zip",
        source_label = "local",
        is_ready_bundle = True,
        install_kind = "windows-cpu",
        expected_sha256 = sha256_file(bundle_archive),
    )

    install_dir = tmp_path / "install"
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    probe_path = tmp_path / "stories260K.gguf"
    quantized_path = tmp_path / "stories260K-q4.gguf"
    validate_prebuilt_choice(
        choice,
        host,
        install_dir,
        work_dir,
        probe_path,
        requested_tag = upstream_tag,
        llama_tag = upstream_tag,
        release_tag = upstream_tag,
        approved_checksums = approved_checksums_for(
            upstream_tag,
            source_archive = source_archive,
            bundle_archive = bundle_archive,
            bundle_name = bundle_name,
        ),
        prebuilt_fallback_used = False,
        quantized_path = quantized_path,
    )

    assert (install_dir / "gguf-py" / "gguf" / "__init__.py").exists()
    assert (install_dir / "convert_hf_to_gguf.py").exists()
    assert (install_dir / "build" / "bin" / "Release" / "llama-server.exe").exists()
    assert (install_dir / "build" / "bin" / "Release" / "llama-quantize.exe").exists()
    assert (install_dir / "build" / "bin" / "Release" / "llama.dll").exists()
    assert not (install_dir / "llama-server.exe").exists()
    assert (install_dir / "UNSLOTH_PREBUILT_INFO.json").exists()
    assert (install_dir / "BUILD_INFO.txt").exists()