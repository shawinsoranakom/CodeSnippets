async def store_sandbox_files(
    extracted_files: list[ExtractedFile],
    execution_context: "ExecutionContext",
) -> list[SandboxFileOutput]:
    """
    Store extracted sandbox files to workspace and return output objects.

    Args:
        extracted_files: List of files extracted from sandbox
        execution_context: Execution context for workspace storage

    Returns:
        List of SandboxFileOutput objects with workspace refs
    """
    outputs: list[SandboxFileOutput] = []

    for file in extracted_files:
        # Decode content for text files (for backward compat content field)
        if file.is_text:
            try:
                content_str = file.content.decode("utf-8", errors="replace")
            except Exception:
                content_str = ""
        else:
            content_str = f"[Binary file: {len(file.content)} bytes]"

        # Build data URI (needed for storage and as binary fallback)
        mime_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        data_uri = f"data:{mime_type};base64,{base64.b64encode(file.content).decode()}"

        # Try to store in workspace
        workspace_ref: str | None = None
        try:
            result = await store_media_file(
                file=MediaFileType(data_uri),
                execution_context=execution_context,
                return_format="for_block_output",
            )
            if result.startswith("workspace://"):
                workspace_ref = result
            elif not file.is_text:
                # Non-workspace context (graph execution): store_media_file
                # returned a data URI — use it as content so binary data isn't lost.
                content_str = result
        except Exception as e:
            logger.warning(f"Failed to store file {file.name} to workspace: {e}")
            # For binary files, fall back to data URI to prevent data loss
            if not file.is_text:
                content_str = data_uri

        outputs.append(
            SandboxFileOutput(
                path=file.path,
                relative_path=file.relative_path,
                name=file.name,
                content=content_str,
                workspace_ref=workspace_ref,
            )
        )

    return outputs