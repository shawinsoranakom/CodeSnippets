def check_sbom_packages(sbom_data: dict[str, typing.Any]) -> None:
    """Make a bunch of assertions about the SBOM package data to ensure it's consistent."""

    for package in sbom_data["packages"]:
        # Properties and ID must be properly formed.
        error_if(
            "name" not in package,
            "Package is missing the 'name' field"
        )

        # Verify that the checksum matches the expected value
        # and that the download URL is valid.
        if "checksums" not in package or "CI" in os.environ:
            download_location = package["downloadLocation"]
            resp = download_with_retries(download_location)
            error_if(resp.status != 200, f"Couldn't access URL: {download_location}'")

            package["checksums"] = [{
                "algorithm": "SHA256",
                "checksumValue": hashlib.sha256(resp.read()).hexdigest()
            }]

        missing_required_keys = REQUIRED_PROPERTIES_PACKAGE - set(package.keys())
        error_if(
            bool(missing_required_keys),
            f"Package '{package['name']}' is missing required fields: {missing_required_keys}",
        )
        error_if(
            package["SPDXID"] != spdx_id(f"SPDXRef-PACKAGE-{package['name']}"),
            f"Package '{package['name']}' has a malformed SPDXID",
        )

        # Version must be in the download and external references.
        version = package["versionInfo"]
        error_if(
            version not in package["downloadLocation"],
            f"Version '{version}' for package '{package['name']} not in 'downloadLocation' field",
        )
        error_if(
            any(version not in ref["referenceLocator"] for ref in package["externalRefs"]),
            (
                f"Version '{version}' for package '{package['name']} not in "
                f"all 'externalRefs[].referenceLocator' fields"
            ),
        )

        # HACL* specifies its expected rev in a refresh script.
        if package["name"] == "hacl-star":
            hacl_refresh_sh = (CPYTHON_ROOT_DIR / "Modules/_hacl/refresh.sh").read_text()
            hacl_expected_rev_match = re.search(
                r"expected_hacl_star_rev=([0-9a-f]{40})",
                hacl_refresh_sh
            )
            hacl_expected_rev = hacl_expected_rev_match and hacl_expected_rev_match.group(1)

            error_if(
                hacl_expected_rev != version,
                "HACL* SBOM version doesn't match value in 'Modules/_hacl/refresh.sh'"
            )

        # libexpat specifies its expected rev in a refresh script.
        if package["name"] == "expat":
            libexpat_refresh_sh = (CPYTHON_ROOT_DIR / "Modules/expat/refresh.sh").read_text()
            libexpat_expected_version_match = re.search(
                r"expected_libexpat_version=\"([0-9]+\.[0-9]+\.[0-9]+)\"",
                libexpat_refresh_sh
            )
            libexpat_expected_sha256_match = re.search(
                r"expected_libexpat_sha256=\"([a-f0-9]{64})\"",
                libexpat_refresh_sh
            )
            libexpat_expected_version = libexpat_expected_version_match and libexpat_expected_version_match.group(1)
            libexpat_expected_sha256 = libexpat_expected_sha256_match and libexpat_expected_sha256_match.group(1)

            error_if(
                libexpat_expected_version != version,
                "libexpat SBOM version doesn't match value in 'Modules/expat/refresh.sh'"
            )
            error_if(
                package["checksums"] != [{
                    "algorithm": "SHA256",
                    "checksumValue": libexpat_expected_sha256
                }],
                "libexpat SBOM checksum doesn't match value in 'Modules/expat/refresh.sh'"
            )

        # License must be on the approved list for SPDX.
        license_concluded = package["licenseConcluded"]
        error_if(
            license_concluded != "NOASSERTION",
            "License identifier must be 'NOASSERTION'"
        )