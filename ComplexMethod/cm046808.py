def test_activate_install_tree_cleans_all_paths_when_rollback_restore_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    install_dir = tmp_path / "llama.cpp"
    install_dir.mkdir()
    (install_dir / "old.txt").write_text("old install\n")

    staging_dir = create_install_staging_dir(install_dir)
    (staging_dir / "new.txt").write_text("new install\n")

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

    monkeypatch.setattr(
        INSTALL_LLAMA_PREBUILT,
        "confirm_install_tree",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("activation confirm failed")
        ),
    )

    original_replace = INSTALL_LLAMA_PREBUILT.os.replace

    def flaky_replace(src, dst):
        src_path = Path(src)
        dst_path = Path(dst)
        if "rollback-" in src_path.name and dst_path == install_dir:
            raise OSError("restore failed")
        return original_replace(src, dst)

    monkeypatch.setattr(INSTALL_LLAMA_PREBUILT.os, "replace", flaky_replace)

    with pytest.raises(
        PrebuiltFallback,
        match = "activation and rollback failed; cleaned install state for fresh source build",
    ):
        activate_install_tree(staging_dir, install_dir, host)

    assert not install_dir.exists()
    assert not staging_dir.exists()
    assert not (tmp_path / ".staging").exists()

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "rollback after failed activation also failed: restore failed" in output
    assert (
        "cleaning staging, install, and rollback paths before source build fallback"
        in output
    )
    assert "removing failed install path" in output
    assert "removing rollback path" in output