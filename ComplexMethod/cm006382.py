async def upsert_flow_from_file(file_content: AnyStr, filename: str, session: AsyncSession, user_id: UUID) -> None:
    flow = orjson.loads(file_content)
    flow_endpoint_name = flow.get("endpoint_name")
    if _is_valid_uuid(filename):
        flow["id"] = filename
    flow_id = flow.get("id")

    if isinstance(flow_id, str):
        try:
            flow_id = UUID(flow_id)
        except ValueError:
            await logger.aerror(f"Invalid UUID string: {flow_id}")
            return

    existing = await find_existing_flow(session, flow_id, flow_endpoint_name)
    if existing:
        await logger.adebug(f"Found existing flow: {existing.name}")
        await logger.ainfo(f"Updating existing flow: {flow_id} with endpoint name {flow_endpoint_name}")
        for key, value in flow.items():
            if hasattr(existing, key):
                # flow dict from json and db representation are not 100% the same
                setattr(existing, key, value)
        existing.updated_at = datetime.now(tz=timezone.utc).astimezone()
        existing.user_id = user_id

        # Ensure that the flow is associated with an existing default folder
        if existing.folder_id is None:
            folder = await get_or_create_default_folder(session, user_id)
            existing.folder_id = folder.id

        if isinstance(existing.id, str):
            try:
                existing.id = UUID(existing.id)
            except ValueError:
                await logger.aerror(f"Invalid UUID string: {existing.id}")
                return

        session.add(existing)
    else:
        await logger.ainfo(f"Creating new flow: {flow_id} with endpoint name {flow_endpoint_name}")

        # Assign the newly created flow to the default folder
        folder = await get_or_create_default_folder(session, user_id)
        flow["user_id"] = user_id
        flow["folder_id"] = folder.id
        flow = Flow.model_validate(flow)
        flow.updated_at = datetime.now(tz=timezone.utc).astimezone()

        session.add(flow)