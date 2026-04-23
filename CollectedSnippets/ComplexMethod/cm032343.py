async def _collect_artifacts(container: str, task_id: str, host_workdir: str) -> list[ArtifactItem]:
    artifacts_path = f"/workspace/{task_id}/artifacts"

    # List files in the artifacts directory inside the container
    returncode, stdout, _ = await async_run_command(
        "docker", "exec", container, "find", artifacts_path,
        "-maxdepth", "1", "-type", "f", timeout=5,
    )
    if returncode != 0 or not stdout.strip():
        return []

    raw_names = [line.split("/")[-1] for line in stdout.strip().splitlines() if line.strip()]
    # Sanitize: reject names with path traversal or control characters
    filenames = [n for n in raw_names if n and "/" not in n and "\\" not in n and ".." not in n and not n.startswith(".")]
    if not filenames:
        return []

    items: list[ArtifactItem] = []

    for fname in filenames[:MAX_ARTIFACT_COUNT]:
        ext = os.path.splitext(fname)[1].lower()
        mime_type = ALLOWED_ARTIFACT_EXTENSIONS.get(ext)
        if not mime_type:
            logger.warning(f"Skipping artifact with disallowed extension: {fname}")
            continue

        file_path = f"{artifacts_path}/{fname}"

        # Check file size inside the container
        returncode, size_str, _ = await async_run_command(
            "docker", "exec", container, "stat", "-c", "%s", file_path, timeout=5,
        )
        if returncode != 0:
            logger.warning(f"Failed to stat artifact {fname}")
            continue

        file_size = int(size_str.strip())
        if file_size > MAX_ARTIFACT_SIZE:
            logger.warning(f"Artifact {fname} too large ({file_size} bytes), skipping")
            continue
        if file_size == 0:
            continue

        # Read file content via docker exec (docker cp doesn't work with gVisor tmpfs)
        returncode, content_b64, stderr = await async_run_command(
            "docker", "exec", container, "base64", file_path, timeout=30,
        )
        if returncode != 0:
            logger.warning(f"Failed to read artifact {fname}: {stderr}")
            continue

        content_b64 = content_b64.replace("\n", "").strip()

        items.append(ArtifactItem(
            name=fname,
            mime_type=mime_type,
            size=file_size,
            content_b64=content_b64,
        ))
        logger.info(f"Collected artifact: {fname} ({file_size} bytes, {mime_type})")

    return items