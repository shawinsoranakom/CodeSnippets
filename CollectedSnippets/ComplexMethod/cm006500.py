async def download_project_flows(
    *,
    session: DbSession,
    project_id: UUID,
    current_user: CurrentActiveUser,
) -> StreamingResponse:
    """Download all flows from project as a zip file."""
    try:
        query = select(Folder).where(Folder.id == project_id, Folder.user_id == current_user.id)
        result = await session.exec(query)
        project = result.first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        flows_query = select(Flow).where(Flow.folder_id == project_id)
        flows_result = await session.exec(flows_query)
        flows = [FlowRead.model_validate(flow, from_attributes=True) for flow in flows_result.all()]

        if not flows:
            raise HTTPException(status_code=404, detail="No flows found in project")

        # Strip API keys then normalise for git-friendly export (sorted keys,
        # volatile fields removed, code fields as line arrays).
        normalised_flows = [normalize_flow_for_export(remove_api_keys(flow.model_dump())) for flow in flows]
        zip_stream = io.BytesIO()

        with zipfile.ZipFile(zip_stream, "w") as zip_file:
            for flow in normalised_flows:
                safe_name = _sanitize_flow_filename(str(flow["name"]), str(flow.get("id", "flow")))
                # Serialise with sorted keys and 2-space indent for stable diffs.
                flow_json = orjson_dumps(flow, sort_keys=True)
                zip_file.writestr(f"{safe_name}.json", flow_json.encode("utf-8"))

        zip_stream.seek(0)

        current_time = datetime.now(tz=timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_time}_{project.name}_flows.zip"

        # URL encode filename handle non-ASCII (ex. Cyrillic)
        encoded_filename = quote(filename)

        return StreamingResponse(
            zip_stream,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        if "No result found" in str(e):
            raise HTTPException(status_code=404, detail="Project not found") from e
        logger.exception("Error downloading project flows for project_id=%s", project_id)
        raise HTTPException(
            status_code=500, detail="An internal error occurred while downloading project flows."
        ) from e