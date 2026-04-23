async def create_flows(
    *,
    session: DbSession,
    flow_list: FlowListCreate,
    current_user: CurrentActiveUser,
):
    """Create multiple new flows."""
    # Guard against duplicate IDs up-front so callers get a clean 422 instead
    # of an unhandled DB IntegrityError.  Use upload_file() for upsert semantics.
    requested_ids = [f.id for f in flow_list.flows if f.id is not None]
    if requested_ids:
        existing_ids = (await session.exec(select(Flow.id).where(col(Flow.id).in_(requested_ids)))).all()
        if existing_ids:
            conflict = ", ".join(str(i) for i in existing_ids)
            msg = (
                f"Flow(s) with the following IDs already exist: {conflict}. "
                "Use the update endpoint or upload_file() for upsert semantics."
            )
            raise HTTPException(status_code=422, detail=msg)

    db_flows = []
    for flow in flow_list.flows:
        flow.user_id = current_user.id
        # Exclude id from model_validate (same reasoning as _new_flow) and apply separately.
        db_flow = Flow.model_validate(flow.model_dump(exclude={"id"}))
        if flow.id is not None:
            db_flow.id = flow.id
        session.add(db_flow)
        db_flows.append(db_flow)

    await session.flush()
    for db_flow in db_flows:
        await session.refresh(db_flow)

    return [FlowRead.model_validate(db_flow, from_attributes=True) for db_flow in db_flows]