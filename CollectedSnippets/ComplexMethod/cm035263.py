def apply_patch(repo_dir: str, patch: str) -> None:
    """Apply a patch to a repository.

    Args:
        repo_dir: The directory containing the repository
        patch: The patch to apply
    """
    diffs = parse_patch(patch)
    for diff in diffs:
        if not diff.header.new_path:
            logger.warning('Could not determine file to patch')
            continue

        # Remove both "a/" and "b/" prefixes from paths
        old_path = (
            os.path.join(
                repo_dir, diff.header.old_path.removeprefix('a/').removeprefix('b/')
            )
            if diff.header.old_path and diff.header.old_path != '/dev/null'
            else None
        )
        new_path = os.path.join(
            repo_dir, diff.header.new_path.removeprefix('a/').removeprefix('b/')
        )

        # Check if the file is being deleted
        if diff.header.new_path == '/dev/null':
            assert old_path is not None
            if os.path.exists(old_path):
                os.remove(old_path)
                logger.info(f'Deleted file: {old_path}')
            continue

        # Handle file rename
        if old_path and new_path and 'rename from' in diff.text:
            # Create parent directory of new path
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            try:
                # Try to move the file directly
                shutil.move(old_path, new_path)
            except shutil.SameFileError:
                # If it's the same file (can happen with directory renames), copy first then remove
                shutil.copy2(old_path, new_path)
                os.remove(old_path)

            # Try to remove empty parent directories
            old_dir = os.path.dirname(old_path)
            while old_dir and old_dir.startswith(repo_dir):
                try:
                    os.rmdir(old_dir)
                    old_dir = os.path.dirname(old_dir)
                except OSError:
                    # Directory not empty or other error, stop trying to remove parents
                    break
            continue

        if old_path:
            # Open the file in binary mode to detect line endings
            with open(old_path, 'rb') as f:
                original_content = f.read()

            # Detect line endings
            if b'\r\n' in original_content:
                newline = '\r\n'
            elif b'\n' in original_content:
                newline = '\n'
            else:
                newline = None  # Let Python decide

            try:
                with open(old_path, 'r', newline=newline) as f:
                    split_content = [x.strip(newline) for x in f.readlines()]
            except UnicodeDecodeError as e:
                logger.error(f'Error reading file {old_path}: {e}')
                split_content = []
        else:
            newline = '\n'
            split_content = []

        if diff.changes is None:
            logger.warning(f'No changes to apply for {old_path}')
            continue

        new_content = apply_diff(diff, split_content)

        # Ensure the directory exists before writing the file
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        # Write the new content using the detected line endings
        with open(new_path, 'w', newline=newline) as f:
            for line in new_content:
                print(line, file=f)

    logger.info('Patch applied successfully')