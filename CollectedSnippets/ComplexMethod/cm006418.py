async def get_flow_by_id_or_name(
    *,
    user_id: str | None = None,
    flow_id: str | None = None,
    flow_name: str | None = None,
) -> Data | None:
    if not user_id:
        msg = "Session is invalid"
        raise ValueError(msg)
    if not (flow_id or flow_name):
        msg = "Flow ID or Flow Name is required"
        raise ValueError(msg)

    # set user provided flow id or flow name.
    # if both are provided, flow_id is used.
    attr, val = None, None
    if flow_name:
        attr = "name"
        val = flow_name
    if flow_id:
        attr = "id"
        val = flow_id
    if not (attr and val):
        msg = "Flow id or Name is required"
        raise ValueError(msg)
    try:
        async with session_scope() as session:
            uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id  # type: ignore[assignment]
            uuid_flow_id_or_name = val  # type: ignore[assignment]
            if isinstance(val, str) and attr == "id":
                uuid_flow_id_or_name = UUID(val)  # type: ignore[assignment]
            stmt = select(Flow).where(Flow.user_id == uuid_user_id).where(getattr(Flow, attr) == uuid_flow_id_or_name)
            flow = (await session.exec(stmt)).first()
            return flow.to_data() if flow else None

    except Exception as e:
        msg = f"Error getting flow by id: {e}"
        raise ValueError(msg) from e