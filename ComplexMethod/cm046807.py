def test_activate_install_tree_restores_existing_install_after_activation_failure(
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

    with pytest.raises(
        PrebuiltFallback,
        match = "activation failed; restored previous install",
    ):
        activate_install_tree(staging_dir, install_dir, host)

    assert (install_dir / "old.txt").read_text() == "old install\n"
    assert not (install_dir / "new.txt").exists()
    assert not staging_dir.exists()
    assert not (tmp_path / ".staging").exists()

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "moving existing install to rollback path" in output
    assert "restored previous install from rollback path" in output