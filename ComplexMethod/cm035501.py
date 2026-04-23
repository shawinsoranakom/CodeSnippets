def build_runtime_image_in_folder(
    base_image: str,
    runtime_builder: RuntimeBuilder,
    build_folder: Path,
    extra_deps: str | None,
    dry_run: bool,
    force_rebuild: bool,
    platform: str | None = None,
    extra_build_args: list[str] | None = None,
    enable_browser: bool = True,
) -> str:
    runtime_image_repo, _ = get_runtime_image_repo_and_tag(base_image)
    lock_tag = (
        f'oh_v{get_version()}_{get_hash_for_lock_files(base_image, enable_browser)}'
    )
    versioned_tag = (
        # truncate the base image to 96 characters to fit in the tag max length (128 characters)
        f'oh_v{get_version()}_{get_tag_for_versioned_image(base_image)}'
    )
    versioned_image_name = f'{runtime_image_repo}:{versioned_tag}'
    source_tag = f'{lock_tag}_{get_hash_for_source_files()}'
    hash_image_name = f'{runtime_image_repo}:{source_tag}'

    logger.info(f'Building image: {hash_image_name}')
    if force_rebuild:
        logger.debug(
            f'Force rebuild: [{runtime_image_repo}:{source_tag}] from scratch.'
        )
        prep_build_folder(
            build_folder,
            base_image,
            build_from=BuildFromImageType.SCRATCH,
            extra_deps=extra_deps,
            enable_browser=enable_browser,
        )
        if not dry_run:
            _build_sandbox_image(
                build_folder,
                runtime_builder,
                runtime_image_repo,
                source_tag,
                lock_tag,
                versioned_tag,
                platform,
                extra_build_args=extra_build_args,
            )
        return hash_image_name

    lock_image_name = f'{runtime_image_repo}:{lock_tag}'
    build_from = BuildFromImageType.SCRATCH

    # If the exact image already exists, we do not need to build it
    if runtime_builder.image_exists(hash_image_name, False):
        logger.debug(f'Reusing Image [{hash_image_name}]')
        return hash_image_name

    # We look for an existing image that shares the same lock_tag. If such an image exists, we
    # can use it as the base image for the build and just copy source files. This makes the build
    # much faster.
    if runtime_builder.image_exists(lock_image_name):
        logger.debug(f'Build [{hash_image_name}] from lock image [{lock_image_name}]')
        build_from = BuildFromImageType.LOCK
        base_image = lock_image_name
    elif runtime_builder.image_exists(versioned_image_name):
        logger.info(
            f'Build [{hash_image_name}] from versioned image [{versioned_image_name}]'
        )
        build_from = BuildFromImageType.VERSIONED
        base_image = versioned_image_name
    else:
        logger.debug(f'Build [{hash_image_name}] from scratch')

    prep_build_folder(build_folder, base_image, build_from, extra_deps, enable_browser)
    if not dry_run:
        _build_sandbox_image(
            build_folder,
            runtime_builder,
            runtime_image_repo,
            source_tag=source_tag,
            lock_tag=lock_tag,
            # Only tag the versioned image if we are building from scratch.
            # This avoids too much layers when you lay one image on top of another multiple times
            versioned_tag=(
                versioned_tag if build_from == BuildFromImageType.SCRATCH else None
            ),
            platform=platform,
            extra_build_args=extra_build_args,
        )

    return hash_image_name