async def validation(
        request: Request, error: ValidationError | ResponseValidationError
    ):
        """Exception handler for ValidationError."""
        # Some validation is performed at Fetcher level.
        # So we check if the validation error comes from a QueryParams class.
        # And that it is in the request query params.
        # If yes, we update the error location with query.
        # If not, we handle it as a base Exception error.
        query_params = dict(request.query_params)
        if isinstance(error, ResponseValidationError):
            detail = [
                {
                    **{k: v for k, v in err.items() if k != "ctx"},
                    "loc": ("query",) + err.get("loc", ()),
                }
                for err in error.errors()
            ]
            return await ExceptionHandlers._handle(
                exception=error,
                status_code=422,
                detail=detail,
            )
        try:
            errors = (
                error.errors(include_url=False)
                if hasattr(error, "errors")
                else error.errors
            )
        except Exception:
            errors = error.errors if hasattr(error, "errors") else error
        all_in_query = all(
            loc in query_params for err in errors for loc in err.get("loc", ())
        )
        if "QueryParams" in error.title and all_in_query:
            detail = [
                {
                    **{k: v for k, v in err.items() if k != "ctx"},
                    "loc": ("query",) + err.get("loc", ()),
                }
                for err in errors
            ]
            return await ExceptionHandlers._handle(
                exception=error,
                status_code=422,
                detail=detail,
            )
        return await ExceptionHandlers.exception(request, error)