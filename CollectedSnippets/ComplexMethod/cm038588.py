async def validation_exception_handler(req: Request, exc: RequestValidationError):
    if req.app.state.args.log_error_stack:
        logger.exception(
            "RequestValidationError caught. Request id: %s",
            req.state.request_metadata.request_id
            if hasattr(req.state, "request_metadata")
            else None,
        )

    param = None
    errors = exc.errors()
    for error in errors:
        if "ctx" in error and "error" in error["ctx"]:
            ctx_error = error["ctx"]["error"]
            if isinstance(ctx_error, VLLMValidationError):
                param = ctx_error.parameter
                break

    exc_str = str(exc)
    errors_str = str(errors)

    if errors and errors_str and errors_str != exc_str:
        message = f"{exc_str} {errors_str}"
    else:
        message = exc_str

    err = ErrorResponse(
        error=ErrorInfo(
            message=sanitize_message(message),
            type=HTTPStatus.BAD_REQUEST.phrase,
            code=HTTPStatus.BAD_REQUEST,
            param=param,
        )
    )
    return JSONResponse(err.model_dump(), status_code=HTTPStatus.BAD_REQUEST)