def check_package_version(
    package: str,
    lt_version: str | None = None,
    lte_version: str | None = None,
    gt_version: str | None = None,
    gte_version: str | None = None,
) -> None:
    """Check the version of a package.

    Args:
        package: The name of the package.
        lt_version: The version must be less than this.
        lte_version: The version must be less than or equal to this.
        gt_version: The version must be greater than this.
        gte_version: The version must be greater than or equal to this.


    Raises:
        ValueError: If the package version does not meet the requirements.
    """
    imported_version = parse(version(package))
    if lt_version is not None and imported_version >= parse(lt_version):
        msg = (
            f"Expected {package} version to be < {lt_version}. Received "
            f"{imported_version}."
        )
        raise ValueError(msg)
    if lte_version is not None and imported_version > parse(lte_version):
        msg = (
            f"Expected {package} version to be <= {lte_version}. Received "
            f"{imported_version}."
        )
        raise ValueError(msg)
    if gt_version is not None and imported_version <= parse(gt_version):
        msg = (
            f"Expected {package} version to be > {gt_version}. Received "
            f"{imported_version}."
        )
        raise ValueError(msg)
    if gte_version is not None and imported_version < parse(gte_version):
        msg = (
            f"Expected {package} version to be >= {gte_version}. Received "
            f"{imported_version}."
        )
        raise ValueError(msg)