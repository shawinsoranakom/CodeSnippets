def test_bump_version() -> None:
    """Make sure it all works."""
    import pytest  # noqa: PLC0415

    assert bump_version(Version("0.56.0"), "beta") == Version("0.56.1b0")
    assert bump_version(Version("0.56.0b3"), "beta") == Version("0.56.0b4")
    assert bump_version(Version("0.56.0.dev0"), "beta") == Version("0.56.0b0")

    assert bump_version(Version("0.56.3"), "dev") == Version("0.57.0.dev0")
    assert bump_version(Version("0.56.0b3"), "dev") == Version("0.57.0.dev0")
    assert bump_version(Version("0.56.0.dev0"), "dev") == Version("0.56.0.dev1")

    assert bump_version(Version("0.56.3"), "patch") == Version("0.56.4")
    assert bump_version(Version("0.56.3.b3"), "patch") == Version("0.56.3")
    assert bump_version(Version("0.56.0.dev0"), "patch") == Version("0.56.0")

    assert bump_version(Version("0.56.0"), "minor") == Version("0.57.0")
    assert bump_version(Version("0.56.3"), "minor") == Version("0.57.0")
    assert bump_version(Version("0.56.0.b3"), "minor") == Version("0.56.0")
    assert bump_version(Version("0.56.3.b3"), "minor") == Version("0.57.0")
    assert bump_version(Version("0.56.0.dev0"), "minor") == Version("0.56.0")
    assert bump_version(Version("0.56.2.dev0"), "minor") == Version("0.57.0")

    now = dt_util.utcnow().strftime("%Y%m%d%H%M")
    assert bump_version(Version("0.56.0.dev0"), "nightly") == Version(
        f"0.56.0.dev{now}"
    )
    assert bump_version(
        Version("2024.4.0.dev20240327"),
        "nightly",
        nightly_version="2024.4.0.dev202403271315",
    ) == Version("2024.4.0.dev202403271315")
    with pytest.raises(ValueError, match="Can only be run on dev release"):
        bump_version(Version("0.56.0"), "nightly")
    with pytest.raises(
        ValueError, match="Nightly version must have the same release version"
    ):
        bump_version(
            Version("0.56.0.dev0"),
            "nightly",
            nightly_version="2024.4.0.dev202403271315",
        )
    with pytest.raises(ValueError, match="Nightly version must be a dev version"):
        bump_version(Version("0.56.0.dev0"), "nightly", nightly_version="0.56.0")