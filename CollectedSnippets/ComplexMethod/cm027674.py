def bump_version(
    version: Version, bump_type: str, *, nightly_version: str | None = None
) -> Version:
    """Return a new version given a current version and action."""
    to_change = {}

    if bump_type == "minor":
        # Convert 0.67.3 to 0.68.0
        # Convert 0.67.3.b5 to 0.68.0
        # Convert 0.67.3.dev0 to 0.68.0
        # Convert 0.67.0.b5 to 0.67.0
        # Convert 0.67.0.dev0 to 0.67.0
        to_change["dev"] = None
        to_change["pre"] = None

        if not version.is_prerelease or version.release[2] != 0:
            to_change["release"] = _bump_release(version.release, "minor")

    elif bump_type == "patch":
        # Convert 0.67.3 to 0.67.4
        # Convert 0.67.3.b5 to 0.67.3
        # Convert 0.67.3.dev0 to 0.67.3
        to_change["dev"] = None
        to_change["pre"] = None

        if not version.is_prerelease:
            to_change["release"] = _bump_release(version.release, "patch")

    elif bump_type == "dev":
        # Convert 0.67.3 to 0.67.4.dev0
        # Convert 0.67.3.b5 to 0.67.4.dev0
        # Convert 0.67.3.dev0 to 0.67.3.dev1
        if version.is_devrelease:
            to_change["dev"] = _get_dev_change(version.dev + 1)
        else:
            to_change["dev"] = _get_dev_change(0)
            to_change["pre"] = None
            to_change["release"] = _bump_release(version.release, "minor")

    elif bump_type == "beta":
        # Convert 0.67.5 to 0.67.6b0
        # Convert 0.67.0.dev0 to 0.67.0b0
        # Convert 0.67.5.b4 to 0.67.5b5

        if version.is_devrelease:
            to_change["dev"] = None
            to_change["pre"] = ("b", 0)

        elif version.is_prerelease:
            if version.pre[0] == "a":
                to_change["pre"] = ("b", 0)
            if version.pre[0] == "b":
                to_change["pre"] = ("b", version.pre[1] + 1)
            else:
                to_change["pre"] = ("b", 0)
                to_change["release"] = _bump_release(version.release, "patch")

        else:
            to_change["release"] = _bump_release(version.release, "patch")
            to_change["pre"] = ("b", 0)

    elif bump_type == "nightly":
        # Convert 0.70.0d0 to 0.70.0d201904241254, fails when run on non dev release
        if not version.is_devrelease:
            raise ValueError("Can only be run on dev release")

        new_dev = dt_util.utcnow().strftime("%Y%m%d%H%M")
        if nightly_version:
            new_version = Version(nightly_version)
            if new_version.release != version.release:
                raise ValueError("Nightly version must have the same release version")
            if not new_version.is_devrelease:
                raise ValueError("Nightly version must be a dev version")
            new_dev = new_version.dev

        if not isinstance(new_dev, int):
            new_dev = int(new_dev)
        to_change["dev"] = _get_dev_change(new_dev)

    else:
        raise ValueError(f"Unsupported type: {bump_type}")

    if _PACKAGING_VERSION_BELOW_26:
        temp = Version("0")
        temp._version = version._version._replace(**to_change)  # noqa: SLF001
        return Version(str(temp))

    return replace(version, **to_change)