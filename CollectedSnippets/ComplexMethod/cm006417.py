async def list_flows_by_folder_id(
    *, user_id: str | None = None, folder_id: str | None = None, order_params: dict | None = None
) -> list[Data]:
    if not user_id:
        msg = "Session is invalid"
        raise ValueError(msg)
    if not folder_id:
        msg = "Folder ID is required"
        raise ValueError(msg)

    if order_params is None:
        order_params = {"column": "updated_at", "direction": "desc"}

    try:
        async with session_scope() as session:
            uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
            uuid_folder_id = UUID(folder_id) if isinstance(folder_id, str) else folder_id
            stmt = (
                select(Flow.id, Flow.name, Flow.updated_at)
                .where(Flow.user_id == uuid_user_id)
                .where(Flow.folder_id == uuid_folder_id)
            )
            if order_params is not None:
                sort_col = getattr(Flow, order_params.get("column", "updated_at"), Flow.updated_at)
                sort_dir = SORT_DISPATCHER.get(order_params.get("direction", "desc"), desc)
                stmt = stmt.order_by(sort_dir(sort_col))

            flows = (await session.exec(stmt)).all()
            return [Data(data=dict(flow._mapping)) for flow in flows]  # noqa: SLF001
    except Exception as e:
        msg = f"Error listing flows: {e}"
        raise ValueError(msg) from e