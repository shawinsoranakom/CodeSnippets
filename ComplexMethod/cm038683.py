async def scale_elastic_ep(raw_request: Request):
    try:
        body = await raw_request.json()
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format") from e

    new_data_parallel_size = body.get("new_data_parallel_size")
    drain_timeout = body.get("drain_timeout", 120)  # Default 2 minutes

    if new_data_parallel_size is None:
        raise HTTPException(
            status_code=400, detail="new_data_parallel_size is required"
        )

    if not isinstance(new_data_parallel_size, int) or new_data_parallel_size <= 0:
        raise HTTPException(
            status_code=400,
            detail="new_data_parallel_size must be a positive integer",
        )

    if not isinstance(drain_timeout, int) or drain_timeout <= 0:
        raise HTTPException(
            status_code=400, detail="drain_timeout must be a positive integer"
        )

    # Set scaling flag to prevent new requests
    set_scaling_elastic_ep(True)
    client = engine_client(raw_request)
    try:
        await client.scale_elastic_ep(new_data_parallel_size, drain_timeout)
        return JSONResponse(
            {
                "message": f"Scaled to {new_data_parallel_size} data parallel engines",
            }
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=408,
            detail="Scale failed due to request drain timeout "
            f"after {drain_timeout} seconds",
        ) from e
    except Exception as e:
        logger.error("Scale failed: %s", e)
        raise HTTPException(status_code=500, detail="Scale failed") from e
    finally:
        set_scaling_elastic_ep(False)