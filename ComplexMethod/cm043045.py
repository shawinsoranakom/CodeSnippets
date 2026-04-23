async def get_requests(status: str = "all", limit: int = 50):
    """Get active and completed requests.

    Args:
        status: Filter by 'active', 'completed', 'success', 'error', or 'all'
        limit: Max number of completed requests to return (default 50)
    """
    # Input validation
    if status not in ["all", "active", "completed", "success", "error"]:
        raise HTTPException(400, f"Invalid status: {status}. Must be one of: all, active, completed, success, error")
    if limit < 1 or limit > 1000:
        raise HTTPException(400, f"Invalid limit: {limit}. Must be between 1 and 1000")

    try:
        monitor = get_monitor()

        if status == "active":
            return {"active": monitor.get_active_requests(), "completed": []}
        elif status == "completed":
            return {"active": [], "completed": monitor.get_completed_requests(limit)}
        elif status in ["success", "error"]:
            return {"active": [], "completed": monitor.get_completed_requests(limit, status)}
        else:  # "all"
            return {
                "active": monitor.get_active_requests(),
                "completed": monitor.get_completed_requests(limit)
            }
    except Exception as e:
        logger.error(f"Error getting requests: {e}")
        raise HTTPException(500, str(e))