def test_validate_prebuilt_choice_creates_repo_shaped_linux_install(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    upstream_tag = "b9998"
    bundle_name = "app-b9998-linux-x64-cuda13-newer.tar.gz"
    source_archive = tmp_path / "source.tar.gz"
    bundle_archive = tmp_path / "bundle.tar.gz"
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
    with tarfile.open(bundle_archive, "w:gz") as archive:
        add_bytes_to_tar(archive, "llama-server", b"#!/bin/sh\nexit 0\n", mode = 0o755)
        add_bytes_to_tar(archive, "llama-quantize", b"#!/bin/sh\nexit 0\n", mode = 0o755)
        add_bytes_to_tar(archive, "libllama.so.0.0.1", b"libllama")
        add_symlink_to_tar(archive, "libllama.so.0", "libllama.so.0.0.1")
        add_symlink_to_tar(archive, "libllama.so", "libllama.so.0")
        add_bytes_to_tar(archive, "libggml.so.0.9.8", b"libggml")
        add_symlink_to_tar(archive, "libggml.so.0", "libggml.so.0.9.8")
        add_symlink_to_tar(archive, "libggml.so", "libggml.so.0")
        add_bytes_to_tar(archive, "libggml-base.so.0.9.8", b"libggml-base")
        add_symlink_to_tar(archive, "libggml-base.so.0", "libggml-base.so.0.9.8")
        add_symlink_to_tar(archive, "libggml-base.so", "libggml-base.so.0")
        add_bytes_to_tar(archive, "libggml-cpu-x64.so.0.9.8", b"libggml-cpu")
        add_symlink_to_tar(archive, "libggml-cpu-x64.so.0", "libggml-cpu-x64.so.0.9.8")
        add_symlink_to_tar(archive, "libggml-cpu-x64.so", "libggml-cpu-x64.so.0")
        add_bytes_to_tar(archive, "libmtmd.so.0.0.1", b"libmtmd")
        add_symlink_to_tar(archive, "libmtmd.so.0", "libmtmd.so.0.0.1")
        add_symlink_to_tar(archive, "libmtmd.so", "libmtmd.so.0")
        add_bytes_to_tar(archive, "BUILD_INFO.txt", b"bundle metadata\n")
        add_bytes_to_tar(archive, "THIRD_PARTY_LICENSES.txt", b"licenses\n")

    source_urls = set(INSTALL_LLAMA_PREBUILT.upstream_source_archive_urls(upstream_tag))

    def fake_download_file(url: str, destination: Path) -> None:
        if url in source_urls:
            destination.write_bytes(source_archive.read_bytes())
            return
        if url == "file://bundle":
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
        system = "Linux",
        machine = "x86_64",
        is_windows = False,
        is_linux = True,
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
        url = "file://bundle",
        source_label = "local",
        is_ready_bundle = True,
        install_kind = "linux-cuda",
        bundle_profile = "cuda13-newer",
        runtime_line = "cuda13",
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
    assert (install_dir / "build" / "bin" / "llama-server").exists()
    assert (install_dir / "build" / "bin" / "llama-quantize").exists()
    assert (install_dir / "build" / "bin" / "libllama.so").exists()
    assert (install_dir / "llama-server").exists()
    assert (install_dir / "llama-quantize").exists()
    assert (install_dir / "UNSLOTH_PREBUILT_INFO.json").exists()
    assert (install_dir / "BUILD_INFO.txt").exists()