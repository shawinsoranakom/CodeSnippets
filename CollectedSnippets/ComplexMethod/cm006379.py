async def copy_profile_pictures() -> None:
    """Asynchronously copies profile pictures from the source directory to the target configuration directory.

    This function copies profile pictures while optimizing I/O operations by:
    1. Using a set to track existing files and avoid redundant filesystem checks
    2. Performing bulk copy operations concurrently using asyncio.gather
    3. Offloading blocking I/O to threads

    The directory structure is:
    profile_pictures/
    ├── People/
    │   └── [profile images]
    └── Space/
        └── [profile images]
    """
    # Get config directory from settings
    config_dir = get_storage_service().settings_service.settings.config_dir
    if config_dir is None:
        msg = "Config dir is not set in the settings"
        raise ValueError(msg)

    # Setup source and target paths
    origin = anyio.Path(__file__).parent / "profile_pictures"
    target = anyio.Path(config_dir) / "profile_pictures"

    if not await origin.exists():
        msg = f"The source folder '{origin}' does not exist."
        raise ValueError(msg)

    # Create target dir if needed
    if not await target.exists():
        await target.mkdir(parents=True, exist_ok=True)

    try:
        # Get set of existing files in target to avoid redundant checks
        target_files = {str(f.relative_to(target)) async for f in target.rglob("*") if await f.is_file()}

        # Define a helper coroutine to copy a single file concurrently
        async def copy_file(src_file, dst_file, rel_path):
            # Create parent directories if needed
            await dst_file.parent.mkdir(parents=True, exist_ok=True)
            # Offload blocking I/O to a thread
            await asyncio.to_thread(shutil.copy2, str(src_file), str(dst_file))
            await logger.adebug(f"Copied file '{rel_path}'")

        tasks = []
        async for src_file in origin.rglob("*"):
            if not await src_file.is_file():
                continue

            rel_path = src_file.relative_to(origin)
            if str(rel_path) not in target_files:
                dst_file = target / rel_path
                tasks.append(copy_file(src_file, dst_file, rel_path))

        if tasks:
            await asyncio.gather(*tasks)

    except Exception as exc:
        await logger.aexception("Error copying profile pictures")
        msg = "An error occurred while copying profile pictures."
        raise RuntimeError(msg) from exc