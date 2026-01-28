async def get_execution_accuracy_trends(
    graph_id: str,
    user_id: Optional[str] = None,
    days_back: int = 30,
    drop_threshold: float = 10.0,
    include_historical: bool = False,
    admin_user_id: str = Security(get_user_id),
) -> AccuracyTrendsResponse:
    """
    Get execution accuracy trends with moving averages and alert detection.
    Simple single-query approach.
    """
    logger.info(
        f"Admin user {admin_user_id} requesting accuracy trends for graph {graph_id}"
    )

    try:
        result = await get_accuracy_trends_and_alerts(
            graph_id=graph_id,
            days_back=days_back,
            user_id=user_id,
            drop_threshold=drop_threshold,
            include_historical=include_historical,
        )

        return result

    except Exception as e:
        logger.exception(f"Error getting accuracy trends for graph {graph_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
