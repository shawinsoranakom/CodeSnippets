def _get_variable_query(
    sender: str | None = None,
    sender_name: str | None = None,
    session_id: str | UUID | None = None,
    context_id: str | None = None,
    order_by: str | None = "timestamp",
    order: str | None = "DESC",
    flow_id: UUID | None = None,
    limit: int | None = None,
):
    stmt = select(MessageTable).where(MessageTable.error == False)  # noqa: E712
    if sender:
        stmt = stmt.where(MessageTable.sender == sender)
    if sender_name:
        stmt = stmt.where(MessageTable.sender_name == sender_name)
    if session_id:
        stmt = stmt.where(MessageTable.session_id == session_id)
    if context_id:
        stmt = stmt.where(MessageTable.context_id == context_id)
    if flow_id:
        stmt = stmt.where(MessageTable.flow_id == flow_id)
    if order_by:
        col = getattr(MessageTable, order_by).desc() if order == "DESC" else getattr(MessageTable, order_by).asc()
        stmt = stmt.order_by(col)
    if limit:
        stmt = stmt.limit(limit)
    return stmt