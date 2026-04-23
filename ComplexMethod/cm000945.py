async def read_file_bytes(
    uri: str,
    user_id: str | None,
    session: ChatSession,
) -> bytes:
    """Resolve *uri* to raw bytes using workspace, local, or E2B path logic.

    Raises :class:`ValueError` if the URI cannot be resolved.
    """
    # Strip MIME fragment (e.g. workspace://id#mime) before dispatching.
    plain = uri.split("#")[0] if uri.startswith("workspace://") else uri

    if plain.startswith("workspace://"):
        if not user_id:
            raise ValueError("workspace:// file references require authentication")
        manager = await get_workspace_manager(user_id, session.session_id)
        ws = parse_workspace_uri(plain)
        try:
            data = await (
                manager.read_file(ws.file_ref)
                if ws.is_path
                else manager.read_file_by_id(ws.file_ref)
            )
        except FileNotFoundError:
            raise ValueError(f"File not found: {plain}")
        except (PermissionError, OSError) as exc:
            raise ValueError(f"Failed to read {plain}: {exc}") from exc
        except (AttributeError, TypeError, RuntimeError) as exc:
            # AttributeError/TypeError: workspace manager returned an
            # unexpected type or interface; RuntimeError: async runtime issues.
            logger.warning("Unexpected error reading %s: %s", plain, exc)
            raise ValueError(f"Failed to read {plain}: {exc}") from exc
        # NOTE: Workspace API does not support pre-read size checks;
        # the full file is loaded before the size guard below.
        if len(data) > _MAX_BARE_REF_BYTES:
            raise ValueError(
                f"File too large ({len(data)} bytes, limit {_MAX_BARE_REF_BYTES})"
            )
        return data

    if is_allowed_local_path(plain, get_sdk_cwd()):
        resolved = os.path.realpath(os.path.expanduser(plain))
        try:
            # Read with a one-byte overshoot to detect files that exceed the limit
            # without a separate os.path.getsize call (avoids TOCTOU race).
            with open(resolved, "rb") as fh:
                data = fh.read(_MAX_BARE_REF_BYTES + 1)
            if len(data) > _MAX_BARE_REF_BYTES:
                raise ValueError(
                    f"File too large (>{_MAX_BARE_REF_BYTES} bytes, "
                    f"limit {_MAX_BARE_REF_BYTES})"
                )
            return data
        except FileNotFoundError:
            raise ValueError(f"File not found: {plain}")
        except OSError as exc:
            raise ValueError(f"Failed to read {plain}: {exc}") from exc

    sandbox = get_current_sandbox()
    if sandbox is not None:
        try:
            remote = resolve_sandbox_path(plain)
        except ValueError as exc:
            raise ValueError(
                f"Path is not allowed (not in workspace, sdk_cwd, or sandbox): {plain}"
            ) from exc
        try:
            data = bytes(await sandbox.files.read(remote, format="bytes"))
        except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
            raise ValueError(f"Failed to read from sandbox: {plain}: {exc}") from exc
        except Exception as exc:
            # E2B SDK raises SandboxException subclasses (NotFoundException,
            # TimeoutException, NotEnoughSpaceException, etc.) which don't
            # inherit from standard exceptions.  Import lazily to avoid a
            # hard dependency on e2b at module level.
            try:
                from e2b.exceptions import SandboxException  # noqa: PLC0415

                if isinstance(exc, SandboxException):
                    raise ValueError(
                        f"Failed to read from sandbox: {plain}: {exc}"
                    ) from exc
            except ImportError:
                pass
            # Re-raise unexpected exceptions (TypeError, AttributeError, etc.)
            # so they surface as real bugs rather than being silently masked.
            raise
        # NOTE: E2B sandbox API does not support pre-read size checks;
        # the full file is loaded before the size guard below.
        if len(data) > _MAX_BARE_REF_BYTES:
            raise ValueError(
                f"File too large ({len(data)} bytes, limit {_MAX_BARE_REF_BYTES})"
            )
        return data

    raise ValueError(
        f"Path is not allowed (not in workspace, sdk_cwd, or sandbox): {plain}"
    )