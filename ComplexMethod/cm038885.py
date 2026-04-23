def generate_index_and_metadata(
    whl_files: list[str],
    wheel_base_dir: Path,
    index_base_dir: Path,
    default_variant: str | None = None,
    alias_to_default: str | None = None,
    comment: str = "",
):
    """
    Generate index for all wheel files.

    Args:
        whl_files (list[str]): List of wheel files (must be directly under `wheel_base_dir`).
        wheel_base_dir (Path): Base directory for wheel files.
        index_base_dir (Path): Base directory to store index files.
        default_variant (str | None): The default variant name, if any.
        alias_to_default (str | None): Alias variant name for the default variant, if any.
        comment (str | None): Optional comment to include in the generated HTML files.

    First, parse all wheel files to extract metadata.
    We need to collect all wheel files for each variant, and generate an index for it (in a subdirectory).
    The index for the default variant (if any) is generated in the root index directory.

    If `default_variant` is provided, all wheels must have variant suffixes, and the default variant index
    is purely a copy of the corresponding variant index, with only the links adjusted.
    Otherwise, all wheels without variant suffixes are treated as the default variant.

    If `alias_to_default` is provided, an additional alias subdirectory is created, it has the same content
    as the default variant index, but the links are adjusted accordingly.

    Index directory structure:
        index_base_dir/ (hosted at wheels.vllm.ai/{nightly,$commit,$version}/)
            index.html  # project list, linking to "vllm/" and other packages, and all variant subdirectories
            vllm/
                index.html # package index, pointing to actual files in wheel_base_dir (relative path)
                metadata.json # machine-readable metadata for all wheels in this package
            cpu/ # cpu variant subdirectory
                index.html
                vllm/
                    index.html
                    metadata.json
            cu129/ # cu129 is actually the alias to default variant
                index.html
                vllm/
                    index.html
                    metadata.json
            cu130/ # cu130 variant subdirectory
                index.html
                vllm/
                    index.html
                    metadata.json
            ...

    metadata.json stores a dump of all wheel files' metadata in a machine-readable format:
        [
            {
                "package_name": "vllm",
                "version": "0.10.2rc2",
                "build_tag": null,
                "python_tag": "cp38",
                "abi_tag": "abi3",
                "platform_tag": "manylinux2014_aarch64",
                "variant": "cu129",
                "filename": "vllm-0.10.2rc2+cu129-cp38-abi3-manylinux2014_aarch64.whl",
                "path": "../vllm-0.10.2rc2%2Bcu129-cp38-abi3-manylinux2014_aarch64.whl" # to be concatenated with the directory URL and URL-encoded
            },
            ...
        ]
    """

    parsed_files = [parse_from_filename(f) for f in whl_files]

    if not parsed_files:
        print("No wheel files found, skipping index generation.")
        return

    # For ROCm builds: inherit variant from vllm wheel
    # All ROCm wheels should share the same variant as vllm
    rocm_variant = None
    for file in parsed_files:
        if (
            file.package_name == "vllm"
            and file.variant
            and file.variant.startswith("rocm")
        ):
            rocm_variant = file.variant
            print(f"Detected ROCm variant from vllm: {rocm_variant}")
            break

    # Apply ROCm variant to all wheels without a variant
    if rocm_variant:
        for file in parsed_files:
            if file.variant is None:
                file.variant = rocm_variant
                print(f"Inherited variant '{rocm_variant}' for {file.filename}")

    # Group by variant
    variant_to_files: dict[str, list[WheelFileInfo]] = {}
    for file in parsed_files:
        variant = file.variant or "default"
        if variant not in variant_to_files:
            variant_to_files[variant] = []
        variant_to_files[variant].append(file)

    print(f"Found variants: {list(variant_to_files.keys())}")

    # sanity check for default variant
    if default_variant:
        if "default" in variant_to_files:
            raise ValueError(
                "All wheel files must have variant suffixes when `default_variant` is specified."
            )
        if default_variant not in variant_to_files:
            raise ValueError(
                f"Default variant '{default_variant}' not found among wheel files."
            )

    if alias_to_default:
        if "default" not in variant_to_files:
            # e.g. only some wheels are uploaded to S3 currently
            print(
                "[WARN] Alias to default variant specified, but no default variant found."
            )
        elif alias_to_default in variant_to_files:
            raise ValueError(
                f"Alias variant name '{alias_to_default}' already exists among wheel files."
            )
        else:
            variant_to_files[alias_to_default] = variant_to_files["default"].copy()
            print(f"Alias variant '{alias_to_default}' created for default variant.")

    # Generate comment in HTML header
    comment_str = f" ({comment})" if comment else ""
    comment_tmpl = f"Generated on {datetime.now().isoformat()}{comment_str}"

    # Generate index for each variant
    subdir_names = set()
    for variant, files in variant_to_files.items():
        if variant == "default":
            variant_dir = index_base_dir
        else:
            variant_dir = index_base_dir / variant
            subdir_names.add(variant)

        variant_dir.mkdir(parents=True, exist_ok=True)

        # gather all package names in this variant (normalized per PEP 503)
        packages = set(normalize_package_name(f.package_name) for f in files)
        if variant == "default":
            # these packages should also appear in the "project list"
            # generate after all variants are processed
            subdir_names = subdir_names.union(packages)
        else:
            # generate project list for this variant directly
            project_list_str = generate_project_list(sorted(packages), comment_tmpl)
            with open(variant_dir / "index.html", "w") as f:
                f.write(project_list_str)

        for package in packages:
            # filter files belonging to this package only (compare normalized names)
            package_files = [
                f for f in files if normalize_package_name(f.package_name) == package
            ]
            package_dir = variant_dir / package
            package_dir.mkdir(parents=True, exist_ok=True)
            index_str, metadata_str = generate_package_index_and_metadata(
                package_files, wheel_base_dir, package_dir, comment
            )
            with open(package_dir / "index.html", "w") as f:
                f.write(index_str)
            with open(package_dir / "metadata.json", "w") as f:
                f.write(metadata_str)

    # Generate top-level project list index
    project_list_str = generate_project_list(sorted(subdir_names), comment_tmpl)
    with open(index_base_dir / "index.html", "w") as f:
        f.write(project_list_str)