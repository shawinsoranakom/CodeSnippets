async def get_reviews_by_node_exec_ids(
    node_exec_ids: list[str], user_id: str
) -> dict[str, PendingHumanReviewModel]:
    """
    Get multiple reviews by their node execution IDs regardless of status.

    Unlike get_pending_reviews_by_node_exec_ids, this returns reviews in any status
    (WAITING, APPROVED, REJECTED). Used for validation in idempotent operations.

    Args:
        node_exec_ids: List of node execution IDs to look up
        user_id: User ID for authorization (only returns reviews belonging to this user)

    Returns:
        Dictionary mapping node_exec_id -> PendingHumanReviewModel for found reviews
    """
    if not node_exec_ids:
        return {}

    reviews = await PendingHumanReview.prisma().find_many(
        where={
            "nodeExecId": {"in": node_exec_ids},
            "userId": user_id,
        }
    )

    if not reviews:
        return {}

    # Split into synthetic (CoPilot) and real IDs for different resolution paths
    synthetic_ids = {
        r.nodeExecId for r in reviews if is_copilot_synthetic_id(r.nodeExecId)
    }
    real_ids = [r.nodeExecId for r in reviews if r.nodeExecId not in synthetic_ids]

    # Batch fetch real node executions to avoid N+1 queries
    node_exec_id_to_node_id: dict[str, str] = {}
    if real_ids:
        node_execs = await AgentNodeExecution.prisma().find_many(
            where={"id": {"in": real_ids}},
        )
        node_exec_id_to_node_id = {ne.id: ne.agentNodeId for ne in node_execs}

    result = {}
    for review in reviews:
        if review.nodeExecId in synthetic_ids:
            node_id = parse_node_id_from_exec_id(review.nodeExecId)
        else:
            node_id = node_exec_id_to_node_id.get(review.nodeExecId, review.nodeExecId)
        result[review.nodeExecId] = PendingHumanReviewModel.from_db(
            review, node_id=node_id
        )

    return result