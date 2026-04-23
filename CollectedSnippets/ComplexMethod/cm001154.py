async def extract_sandbox_files(
    sandbox: "BaseAsyncSandbox",
    working_directory: str,
    since_timestamp: str | None = None,
    text_only: bool = True,
) -> list[ExtractedFile]:
    """
    Extract files from an E2B sandbox.

    Args:
        sandbox: The E2B sandbox instance
        working_directory: Directory to search for files
        since_timestamp: ISO timestamp - only return files modified after this time
        text_only: If True, only extract text files (default). If False, extract all files.

    Returns:
        List of ExtractedFile objects with path, content, and metadata
    """
    files: list[ExtractedFile] = []

    try:
        # Build find command
        safe_working_dir = shlex.quote(working_directory)
        timestamp_filter = ""
        if since_timestamp:
            timestamp_filter = f"-newermt {shlex.quote(since_timestamp)} "

        find_result = await sandbox.commands.run(
            f"find {safe_working_dir} -type f "
            f"{timestamp_filter}"
            f"-not -path '*/node_modules/*' "
            f"-not -path '*/.git/*' "
            f"2>/dev/null"
        )

        if not find_result.stdout:
            return files

        for file_path in find_result.stdout.strip().split("\n"):
            if not file_path:
                continue

            # Check if it's a text file
            is_text = any(file_path.endswith(ext) for ext in TEXT_EXTENSIONS)

            # Skip non-text files if text_only mode
            if text_only and not is_text:
                continue

            try:
                # Read file content as bytes
                content = await sandbox.files.read(file_path, format="bytes")
                if isinstance(content, str):
                    content = content.encode("utf-8")
                elif isinstance(content, bytearray):
                    content = bytes(content)

                # Extract filename from path
                file_name = file_path.split("/")[-1]

                # Calculate relative path
                relative_path = file_path
                if file_path.startswith(working_directory):
                    relative_path = file_path[len(working_directory) :]
                    if relative_path.startswith("/"):
                        relative_path = relative_path[1:]

                files.append(
                    ExtractedFile(
                        path=file_path,
                        relative_path=relative_path,
                        name=file_name,
                        content=content,
                        is_text=is_text,
                    )
                )
            except Exception as e:
                logger.debug(f"Failed to read file {file_path}: {e}")
                continue

    except Exception as e:
        logger.warning(f"File extraction failed: {e}")

    return files