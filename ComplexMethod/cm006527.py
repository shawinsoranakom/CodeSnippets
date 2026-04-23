async def get_workflow_status(
    api_key_user: Annotated[UserRead, Depends(api_key_security)],
    job_id: Annotated[JobId | None, Query(description="Job ID to query")] = None,
    session: Annotated[object, Depends(injectable_session_scope_readonly)] = None,
) -> WorkflowExecutionResponse | WorkflowJobResponse:
    """Get workflow job status and results.

    Args:
        api_key_user: Authenticated user from API key
        job_id: Optional job ID to query specific job
        session: Database session for querying vertex builds

    Returns:
        WorkflowExecutionResponse or reconstructed results

    Raises:
        HTTPException:
            - 400: Job ID not provided
            - 403: Developer API disabled or unauthorized
            - 404: Job not found
            - 408: Execution timeout
            - 500: Internal server error or Job failure
    """
    if not job_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Missing required parameter",
                "code": "MISSING_PARAMETER",
                "message": "Job ID must be provided",
            },
        )

    job_service = get_job_service()
    try:
        job = await job_service.get_job_by_job_id(job_id=job_id, user_id=api_key_user.id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"Failed to retrieve job from database: {exc!s}",
            },
        ) from exc

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow job not found",
                "code": "JOB_NOT_FOUND",
                "message": f"Workflow job {job_id} not found",
                "job_id": str(job_id),
            },
        )

    # Verify this is a workflow job
    if job.type != JobType.WORKFLOW:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Workflow job not found",
                "code": "JOB_NOT_FOUND",
                "message": f"Job {job_id} is not a workflow job (type: {job.type})",
                "job_id": str(job_id),
            },
        )

    # Store context for exception handling scope
    flow_id_str = str(job.flow_id)
    job_id_str = str(job_id)
    try:
        # If job is completed, reconstruct full workflow response from vertex_builds
        if job.status == JobStatus.COMPLETED:
            # Get the flow
            flow = await get_flow_by_id_or_endpoint_name(flow_id_str, api_key_user.id)

            # Reconstruct response from vertex_build table
            return await reconstruct_workflow_response_from_job_id(
                session=session,
                flow=flow,
                job_id=job_id_str,
                user_id=str(api_key_user.id),
            )

        if job.status == JobStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Job failed",
                    "code": "JOB_FAILED",
                    "message": f"Job {job_id_str} has failed execution.",
                    "job_id": job_id_str,
                },
            )

        if job.status == JobStatus.TIMED_OUT:
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail={
                    "error": "Execution timeout",
                    "code": "EXECUTION_TIMEOUT",
                    "message": "Workflow execution timed out",
                    "job_id": job_id_str,
                    "flow_id": flow_id_str,
                },
            )

        # Default response for active statuses (QUEUED, IN_PROGRESS, etc.)
        return WorkflowJobResponse(
            flow_id=flow_id_str,
            job_id=job_id_str,
            status=job.status,
        )

    except HTTPException:
        raise
    except WorkflowTimeoutError as err:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={
                "error": "Execution timeout",
                "code": "EXECUTION_TIMEOUT",
                "message": f"Workflow execution exceeded {EXECUTION_TIMEOUT} seconds",
                "job_id": job_id_str,
                "flow_id": flow_id_str,
                "timeout_seconds": EXECUTION_TIMEOUT,
            },
        ) from err
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"Failed to process job status: {exc!s}",
            },
        ) from exc