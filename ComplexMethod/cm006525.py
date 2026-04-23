async def execute_workflow(
    workflow_request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    api_key_user: Annotated[UserRead, Depends(api_key_security)],
) -> WorkflowExecutionResponse | WorkflowJobResponse | StreamingResponse:
    """Execute a workflow with support for multiple execution modes.

    **background** and **stream** can't be true at the same time.
    This endpoint supports three execution modes:
        - **Synchronous** (background=False, stream=False): Returns complete results immediately
        - **Streaming** (stream=True): Returns server-sent events in real-time (not yet implemented)
        - **Background** (background=True): Starts job and returns job ID (not yet implemented)

    Error Handling Strategy:
        - System errors (404, 500, 503, 504): Returned as HTTP error responses
        - Component execution errors: Returned as HTTP 200 with errors in response body

    Args:
        workflow_request: The workflow execution request containing flow_id, inputs, and mode flags
        background_tasks: FastAPI background tasks for async operations
        http_request: The HTTP request object for extracting headers
        api_key_user: Authenticated user from API key

    Returns:
        - WorkflowExecutionResponse: For synchronous execution (HTTP 200)
        - WorkflowJobResponse: For background execution (HTTP 202, not yet implemented)
        - StreamingResponse: For streaming execution (not yet implemented)

    Raises:
        HTTPException:
            - 403: Developer API disabled
            - 404: Flow not found or user lacks access
            - 500: Invalid flow data or validation error
            - 501: Streaming or background mode not yet implemented
            - 503: Database unavailable
            - 504: Execution timeout exceeded
    """
    job_id = uuid4()

    try:
        # Validate flow exists and user has permission
        flow = await get_flow_by_id_or_endpoint_name(workflow_request.flow_id, api_key_user.id)

        # Background mode execution
        if workflow_request.background:
            return await execute_workflow_background(
                workflow_request=workflow_request,
                flow=flow,
                job_id=job_id,
                api_key_user=api_key_user,
                http_request=http_request,
            )

        # Streaming mode (to be implemented)
        if workflow_request.stream:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail={
                    "error": "Not implemented",
                    "code": "NOT_IMPLEMENTED",
                    "message": "Streaming execution not yet implemented",
                },
            )

        # Synchronous execution (default)
        return await execute_sync_workflow_with_timeout(
            workflow_request=workflow_request,
            flow=flow,
            job_id=job_id,
            api_key_user=api_key_user,
            background_tasks=background_tasks,
            http_request=http_request,
        )

    except HTTPException as e:
        # Reformat 404 from get_flow_by_id_or_endpoint_name to structured format
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Flow not found",
                    "code": "FLOW_NOT_FOUND",
                    "message": f"Flow '{workflow_request.flow_id}' does not exist. Verify the flow_id and try again.",
                    "flow_id": workflow_request.flow_id,
                },
            ) from e
        raise
    except OperationalError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Service unavailable, Please try again.",
                "code": "DATABASE_ERROR",
                "message": f"Failed to fetch flow: {e!s}",
                "flow_id": workflow_request.flow_id,
            },
        ) from e
    except WorkflowTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={
                "error": "Execution timeout",
                "code": "EXECUTION_TIMEOUT",
                "message": f"Workflow execution exceeded {EXECUTION_TIMEOUT} seconds",
                "job_id": str(job_id),
                "flow_id": str(workflow_request.flow_id),
                "timeout_seconds": EXECUTION_TIMEOUT,
            },
        ) from None
    except (PydanticValidationError, WorkflowValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Workflow validation error",
                "code": "INVALID_FLOW_DATA",
                "message": str(e),
                "flow_id": workflow_request.flow_id,
            },
        ) from e
    except WorkflowServiceUnavailableError as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Service unavailable",
                "code": "QUEUE_SERVICE_UNAVAILABLE",
                "message": str(err),
                "flow_id": workflow_request.flow_id,
            },
        ) from err
    except (WorkflowResourceError, WorkflowQueueFullError, MemoryError) as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Service busy",
                "code": "SERVICE_BUSY",
                "message": "The service is currently unable to handle the request due to resource limits.",
                "flow_id": workflow_request.flow_id,
            },
        ) from err
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"An unexpected error occurred: {err!s}",
                "flow_id": workflow_request.flow_id,
            },
        ) from err