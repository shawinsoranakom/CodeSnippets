def extract_langflow_artifact_from_zip(artifact_zip_bytes: bytes, *, snapshot_id: str) -> dict[str, Any]:
    """Read and parse the Langflow flow JSON from a wxO snapshot artifact zip."""
    try:
        with zipfile.ZipFile(io.BytesIO(artifact_zip_bytes), "r") as zip_artifact:
            json_members = [name for name in zip_artifact.namelist() if name.lower().endswith(".json")]
            if not json_members:
                msg = f"Snapshot '{snapshot_id}' artifact does not include a flow JSON file."
                raise InvalidContentError(message=msg)

            flow_json_member = json_members[0]
            flow_json_raw = zip_artifact.read(flow_json_member)
    except InvalidContentError:
        raise
    except zipfile.BadZipFile as exc:
        msg = f"Snapshot '{snapshot_id}' artifact is not a valid zip archive."
        raise InvalidContentError(message=msg) from exc

    try:
        return json.loads(flow_json_raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        msg = f"Snapshot '{snapshot_id}' flow artifact is not valid UTF-8 JSON."
        raise InvalidContentError(message=msg) from exc
    except json.JSONDecodeError as exc:
        msg = f"Snapshot '{snapshot_id}' flow artifact contains invalid JSON."
        raise InvalidContentError(message=msg) from exc