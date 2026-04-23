async def admin_get_user_history(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    transaction_filter: CreditTransactionType | None = None,
) -> UserHistoryResponse:

    if page < 1 or page_size < 1:
        raise ValueError("Invalid pagination input")

    where_clause: CreditTransactionWhereInput = {}
    if transaction_filter:
        where_clause["type"] = transaction_filter
    if search:
        where_clause["OR"] = [
            {"userId": {"contains": search, "mode": "insensitive"}},
            {"User": {"is": {"email": {"contains": search, "mode": "insensitive"}}}},
            {"User": {"is": {"name": {"contains": search, "mode": "insensitive"}}}},
        ]
    transactions = await CreditTransaction.prisma().find_many(
        where=where_clause,
        skip=(page - 1) * page_size,
        take=page_size,
        include={"User": True},
        order={"createdAt": "desc"},
    )
    total = await CreditTransaction.prisma().count(where=where_clause)
    total_pages = (total + page_size - 1) // page_size

    history = []
    for tx in transactions:
        admin_id = ""
        admin_email = ""
        reason = ""

        metadata: dict = cast(dict, tx.metadata) or {}

        if metadata:
            admin_id = metadata.get("admin_id")
            admin_email = (
                (await get_user_email_by_id(admin_id) or f"Unknown Admin: {admin_id}")
                if admin_id
                else ""
            )
            reason = metadata.get("reason", "No reason provided")

        user_credit_model = await get_user_credit_model(tx.userId)
        balance, _ = await user_credit_model._get_credits(tx.userId)

        history.append(
            UserTransaction(
                transaction_key=tx.transactionKey,
                transaction_time=tx.createdAt,
                transaction_type=tx.type,
                amount=tx.amount,
                current_balance=balance,
                running_balance=tx.runningBalance or 0,
                user_id=tx.userId,
                user_email=(
                    tx.User.email
                    if tx.User
                    else (await get_user_by_id(tx.userId)).email
                ),
                reason=reason,
                admin_email=admin_email,
                extra_data=str(metadata),
            )
        )
    return UserHistoryResponse(
        history=history,
        pagination=Pagination(
            total_items=total,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        ),
    )