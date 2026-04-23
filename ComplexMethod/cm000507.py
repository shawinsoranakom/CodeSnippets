async def get_transaction_history(
        self,
        user_id: str,
        transaction_count_limit: int | None = 100,
        transaction_time_ceiling: datetime | None = None,
        transaction_type: str | None = None,
    ) -> TransactionHistory:
        transactions_filter: CreditTransactionWhereInput = {
            "userId": user_id,
            "isActive": True,
        }
        if transaction_time_ceiling:
            transaction_time_ceiling = transaction_time_ceiling.replace(
                tzinfo=timezone.utc
            )
            transactions_filter["createdAt"] = {"lt": transaction_time_ceiling}
        if transaction_type:
            transactions_filter["type"] = CreditTransactionType[transaction_type]
        transactions = await CreditTransaction.prisma().find_many(
            where=transactions_filter,
            order={"createdAt": "desc"},
            take=transaction_count_limit,
        )

        # doesn't fill current_balance, reason, user_email, admin_email, or extra_data
        grouped_transactions: dict[str, UserTransaction] = defaultdict(
            lambda: UserTransaction(user_id=user_id)
        )
        tx_time = None
        for t in transactions:
            metadata = (
                UsageTransactionMetadata.model_validate(t.metadata)
                if t.metadata
                else UsageTransactionMetadata()
            )
            tx_time = t.createdAt.replace(tzinfo=timezone.utc)

            if t.type == CreditTransactionType.USAGE and metadata.graph_exec_id:
                gt = grouped_transactions[metadata.graph_exec_id]
                gid = metadata.graph_id[:8] if metadata.graph_id else "UNKNOWN"
                gt.description = f"Graph #{gid} Execution"

                gt.usage_node_count += 1
                gt.usage_start_time = min(gt.usage_start_time, tx_time)
                gt.usage_execution_id = metadata.graph_exec_id
                gt.usage_graph_id = metadata.graph_id
            else:
                gt = grouped_transactions[t.transactionKey]
                gt.description = f"{t.type} Transaction"
                gt.transaction_key = t.transactionKey

            gt.amount += t.amount
            gt.transaction_type = t.type

            if tx_time > gt.transaction_time:
                gt.transaction_time = tx_time
                gt.running_balance = t.runningBalance or 0

        return TransactionHistory(
            transactions=list(grouped_transactions.values()),
            next_transaction_time=(
                tx_time if len(transactions) == transaction_count_limit else None
            ),
        )