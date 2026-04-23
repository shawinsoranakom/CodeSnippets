async def list_flows_by_flow_folder(
    *,
    user_id: str | None = None,
    flow_id: str | None = None,
    order_params: dict | None = {"column": "updated_at", "direction": "desc"},  # noqa: B006
) -> list[Data]:
    if not user_id:
        msg = "Session is invalid"
        raise ValueError(msg)
    if not flow_id:
        msg = "Flow ID is required"
        raise ValueError(msg)
    try:
        async with session_scope() as session:
            uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
            uuid_flow_id = UUID(flow_id) if isinstance(flow_id, str) else flow_id
            # get all flows belonging to the specified user
            # and inside the same folder as the specified flow
            flow_ = aliased(Flow)  # flow table alias, used to retrieve the folder
            stmt = (
                select(Flow.id, Flow.name, Flow.updated_at)
                .join(flow_, Flow.folder_id == flow_.folder_id)
                .where(flow_.id == uuid_flow_id)
                .where(flow_.user_id == uuid_user_id)
                .where(Flow.user_id == uuid_user_id)
                .where(Flow.id != uuid_flow_id)
            )
            # sort flows by the specified column and direction
            if order_params is not None:
                sort_col = getattr(Flow, order_params.get("column", "updated_at"), Flow.updated_at)
                sort_dir = SORT_DISPATCHER.get(order_params.get("direction", "desc"), desc)
                stmt = stmt.order_by(sort_dir(sort_col))

            flows = (await session.exec(stmt)).all()
            return [Data(data=dict(flow._mapping)) for flow in flows]  # noqa: SLF001
    except Exception as e:
        msg = f"Error listing flows: {e}"
        raise ValueError(msg) from e