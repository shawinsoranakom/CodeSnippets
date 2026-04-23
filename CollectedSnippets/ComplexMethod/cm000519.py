async def process_all_reviews_for_execution(
    user_id: str,
    review_decisions: dict[str, tuple[ReviewStatus, SafeJsonData | None, str | None]],
) -> dict[str, PendingHumanReviewModel]:
    """Process all pending reviews for an execution with approve/reject decisions.

    Handles race conditions gracefully: if a review was already processed with the
    same decision by a concurrent request, it's treated as success rather than error.

    Args:
        user_id: User ID for ownership validation
        review_decisions: Map of node_exec_id -> (status, reviewed_data, message)

    Returns:
        Dict of node_exec_id -> updated review model (includes already-processed reviews)
    """
    if not review_decisions:
        return {}

    node_exec_ids = list(review_decisions.keys())

    # Get all reviews (both WAITING and already processed) for the user
    all_reviews = await PendingHumanReview.prisma().find_many(
        where={
            "nodeExecId": {"in": node_exec_ids},
            "userId": user_id,
        },
    )

    # Separate into pending and already-processed reviews
    reviews_to_process = []
    already_processed = []
    for review in all_reviews:
        if review.status == ReviewStatus.WAITING:
            reviews_to_process.append(review)
        else:
            already_processed.append(review)

    # Check for truly missing reviews (not found at all)
    found_ids = {review.nodeExecId for review in all_reviews}
    missing_ids = set(node_exec_ids) - found_ids
    if missing_ids:
        raise ValueError(
            f"Reviews not found or access denied: {', '.join(missing_ids)}"
        )

    # Validate already-processed reviews have compatible status (same decision)
    # This handles race conditions where another request processed the same reviews
    for review in already_processed:
        requested_status = review_decisions[review.nodeExecId][0]
        if review.status != requested_status:
            raise ValueError(
                f"Review {review.nodeExecId} was already processed with status "
                f"{review.status}, cannot change to {requested_status}"
            )

    # Log if we're handling a race condition (some reviews already processed)
    if already_processed:
        already_processed_ids = [r.nodeExecId for r in already_processed]
        logger.info(
            f"Race condition handled: {len(already_processed)} review(s) already "
            f"processed by concurrent request: {already_processed_ids}"
        )

    # Create parallel update tasks for reviews that still need processing
    update_tasks = []

    for review in reviews_to_process:
        new_status, reviewed_data, message = review_decisions[review.nodeExecId]
        has_data_changes = reviewed_data is not None and reviewed_data != review.payload

        # Check edit permissions for actual data modifications
        if has_data_changes and not review.editable:
            raise ValueError(f"Review {review.nodeExecId} is not editable")

        update_data: PendingHumanReviewUpdateInput = {
            "status": new_status,
            "reviewMessage": message,
            "wasEdited": has_data_changes,
            "reviewedAt": datetime.now(timezone.utc),
        }

        if has_data_changes:
            update_data["payload"] = SafeJson(reviewed_data)

        task = PendingHumanReview.prisma().update(
            where={"nodeExecId": review.nodeExecId},
            data=update_data,
        )
        update_tasks.append(task)

    # Execute all updates in parallel and get updated reviews
    updated_reviews = await asyncio.gather(*update_tasks) if update_tasks else []

    # Note: Execution resumption is now handled at the API layer after ALL reviews
    # for an execution are processed (both approved and rejected)

    # Fetch node_id for each review and return as dict for easy access
    # Local import to avoid event loop conflicts in tests
    from backend.data.execution import get_node_execution

    # Combine updated reviews with already-processed ones (for idempotent response)
    all_result_reviews = list(updated_reviews) + already_processed

    result = {}
    for review in all_result_reviews:
        if is_copilot_synthetic_id(review.nodeExecId):
            # CoPilot synthetic node_exec_ids encode node_id as "{node_id}:{random}"
            node_id = parse_node_id_from_exec_id(review.nodeExecId)
        else:
            node_exec = await get_node_execution(review.nodeExecId)
            node_id = node_exec.node_id if node_exec else review.nodeExecId
        result[review.nodeExecId] = PendingHumanReviewModel.from_db(
            review, node_id=node_id
        )

    return result