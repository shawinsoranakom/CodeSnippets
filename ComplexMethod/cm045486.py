async def list_session_runs(session_id: int, user_id: str, db=Depends(get_db)) -> Dict:
    """Get complete session history organized by runs"""

    try:
        # 1. Verify session exists and belongs to user
        session = db.get(Session, filters={"id": session_id, "user_id": user_id}, return_json=False)
        if not session.status:
            raise HTTPException(status_code=500, detail="Database error while fetching session")
        if not session.data:
            raise HTTPException(status_code=404, detail="Session not found or access denied")

        # 2. Get ordered runs for session
        runs = db.get(Run, filters={"session_id": session_id}, order="asc", return_json=False)
        if not runs.status:
            raise HTTPException(status_code=500, detail="Database error while fetching runs")

        # 3. Build response with messages per run
        run_data = []
        if runs.data:  # It's ok to have no runs
            for run in runs.data:
                try:
                    # Get messages for this specific run
                    messages = db.get(Message, filters={"run_id": run.id}, order="asc", return_json=False)
                    if not messages.status:
                        logger.error(f"Failed to fetch messages for run {run.id}")
                        # Continue processing other runs even if one fails
                        messages.data = []

                    run_data.append(
                        {
                            "id": str(run.id),
                            "created_at": run.created_at,
                            "status": run.status,
                            "task": run.task,
                            "team_result": run.team_result,
                            "messages": messages.data or [],
                        }
                    )
                except Exception as e:
                    logger.error(f"Error processing run {run.id}: {str(e)}")
                    # Include run with error state instead of failing entirely
                    run_data.append(
                        {
                            "id": str(run.id),
                            "created_at": run.created_at,
                            "status": "ERROR",
                            "task": run.task,
                            "team_result": None,
                            "messages": [],
                            "error": f"Failed to process run: {str(e)}",
                        }
                    )

        return {"status": True, "data": {"runs": run_data}}

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error in list_messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching session data") from e