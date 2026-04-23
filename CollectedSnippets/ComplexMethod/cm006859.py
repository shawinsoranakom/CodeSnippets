def _upsert_single(
    client: Any,
    sdk: Any,
    path: Path,
    flow_id: UUID,
    flow_create: Any,
    *,
    dry_run: bool,
    flow_name: str,
    base_url: str,
    local_file_content: str | None = None,
    strip_secrets: bool = True,
) -> PushResult:
    flow_url = f"{base_url.rstrip('/')}/flow/{flow_id}"

    if dry_run:
        return PushResult(path=path, flow_id=flow_id, flow_name=flow_name, status="dry-run", flow_url=flow_url)

    # Compare normalized remote against local file to detect unchanged flows,
    # avoiding a spurious PUT when nothing has actually changed.
    # Import directly from serialization so this internal comparison is not
    # counted as a call to the public sdk.normalize_flow (keeps tests clean).
    if local_file_content is not None:
        try:
            # Use direct module imports (not sdk.*) so mock call-counts in tests
            # stay accurate and so the except clause uses a real exception class.
            from langflow_sdk.exceptions import LangflowNotFoundError
            from langflow_sdk.serialization import flow_to_json, normalize_flow

            remote = client.get_flow(flow_id)
            remote_normalized = normalize_flow(
                remote.model_dump(mode="json"),
                strip_volatile=True,
                strip_secrets=strip_secrets,
                sort_keys=True,
            )
            if flow_to_json(remote_normalized) == local_file_content:
                return PushResult(
                    path=path,
                    flow_id=flow_id,
                    flow_name=flow_name,
                    status="unchanged",
                    flow_url=flow_url,
                )
        except LangflowNotFoundError:
            pass  # Flow doesn't exist yet — fall through to create it
        except Exception:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).debug("Remote comparison failed; proceeding with push", exc_info=True)

    try:
        _, created = client.upsert_flow(flow_id, flow_create)
        status = "created" if created else "updated"
        return PushResult(path=path, flow_id=flow_id, flow_name=flow_name, status=status, flow_url=flow_url)
    except sdk.LangflowHTTPError as exc:
        return PushResult(
            path=path,
            flow_id=flow_id,
            flow_name=flow_name,
            status="error",
            error=str(exc),
            flow_url=flow_url,
        )