async def get_messages(
    session: DbSession,
    current_user: Annotated[User, Depends(get_current_active_user)],
    flow_id: Annotated[UUID | None, Query()] = None,
    session_id: Annotated[str | None, Query()] = None,
    sender: Annotated[str | None, Query()] = None,
    sender_name: Annotated[str | None, Query()] = None,
    order_by: Annotated[str | None, Query()] = "timestamp",
) -> list[MessageResponse]:
    try:
        # Use JOIN instead of subquery for better performance
        stmt = select(MessageTable)
        stmt = stmt.join(Flow, MessageTable.flow_id == Flow.id)
        stmt = stmt.where(Flow.user_id == current_user.id)

        if flow_id:
            stmt = stmt.where(MessageTable.flow_id == flow_id)
        if session_id:
            from urllib.parse import unquote

            decoded_session_id = unquote(session_id)
            stmt = stmt.where(MessageTable.session_id == decoded_session_id)
        if sender:
            stmt = stmt.where(MessageTable.sender == sender)
        if sender_name:
            stmt = stmt.where(MessageTable.sender_name == sender_name)
        if order_by:
            order_col = getattr(MessageTable, order_by).asc()
            stmt = stmt.order_by(order_col)
        messages = await session.exec(stmt)
        return [MessageResponse.model_validate(d, from_attributes=True) for d in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e