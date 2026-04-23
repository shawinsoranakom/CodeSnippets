def get_next_version(version: Version, /, final: bool = False, pre: str | None = None, mode: VersionMode = VersionMode.DEFAULT) -> Version:
    """Return the next version after the specified version."""

    # TODO: consider using development versions instead of post versions after a release is published

    pre = pre or ""
    micro = version.micro

    if version.is_devrelease:
        # The next version of a development release is the same version without the development component.
        if final:
            pre = ""
        elif not pre and version.pre is not None:
            pre = f"{version.pre[0]}{version.pre[1]}"
        elif not pre:
            pre = "b1"  # when there is no existing pre and none specified, advance to b1

    elif version.is_postrelease:
        # The next version of a post release is the next pre-release *or* micro release component.
        if final:
            pre = ""
        elif not pre and version.pre is not None:
            pre = f"{version.pre[0]}{version.pre[1] + 1}"
        elif not pre:
            pre = "rc1"  # when there is no existing pre and none specified, advance to rc1

        if version.pre is None:
            micro = version.micro + 1
    else:
        raise ApplicationError(f"Version {version} is not a development or post release version.")

    version = f"{version.major}.{version.minor}.{micro}{pre}"

    return get_ansible_version(version, mode=mode)