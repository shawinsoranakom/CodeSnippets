async def upload_file(
    *,
    session: DbSession,
    file: Annotated[UploadFile | None, File()] = None,
    current_user: CurrentActiveUser,
    folder_id: UUID | None = None,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
):
    """Upload flows from a JSON or ZIP file (upsert semantics for flows with stable IDs)."""
    if file is None:
        raise HTTPException(status_code=400, detail="No file provided")

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    if zipfile.is_zipfile(io.BytesIO(contents)):
        try:
            flows_data = await extract_flows_from_zip(contents)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        if not flows_data:
            raise HTTPException(status_code=400, detail="No valid flow JSON files found in the ZIP")
        data = {"flows": flows_data}
    else:
        try:
            data = orjson.loads(contents)
        except orjson.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}") from e

    # Normalise code fields: if exported with code-as-lines format, rejoin to
    # strings before creating the Pydantic models so the DB always stores strings.
    if "flows" in data:
        data = {**data, "flows": [normalize_code_for_import(f) for f in data["flows"]]}
        flow_list = FlowListCreate(**data)
    else:
        flow_list = FlowListCreate(flows=[FlowCreate(**normalize_code_for_import(data))])

    # TODO: Full-version import is planned as a follow-up feature.
    # When implemented, extract raw flow dicts here to read embedded "version"
    # arrays and create FlowVersion entries for each imported flow.

    try:
        return await _upsert_flow_list(
            session=session,
            flows=flow_list.flows,
            current_user=current_user,
            storage_service=storage_service,
            folder_id=folder_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_unique_constraint_error(e) from e